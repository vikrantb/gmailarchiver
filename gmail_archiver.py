import os
import datetime
import time
import base64
import email
import shutil
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from email import policy
from email.parser import BytesParser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailArchiver:
    """
    A tool to archive Gmail emails within a specified date range.
    It backs up emails to local storage, organizes them by year and month,
    compresses them, and optionally deletes them from the Gmail account.
    """

    # Define the Gmail API scope
    SCOPES = ["https://mail.google.com/"]

    def __init__(self):
        """
        Initializes the GmailArchiver with user inputs and default values.
        """
        print("Welcome to the Gmail Archiver!")

        # Confirm if the user wants to delete emails after archiving
        self.delete_after_archive = self.prompt_for_confirmation(
            "Do you want to delete the emails from your Gmail account after archiving? (yes/no): ")

        # Prompt user for base path
        self.base_path = input("Enter the base path for archiving (press Enter to use the current directory): ").strip()
        if not self.base_path:
            self.base_path = os.getcwd()
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        # Set save path for emails
        self.save_path = os.path.join(self.base_path, "emails")

        # Path to the log file
        self.log_file = os.path.join(self.base_path, "email_progress.log")

        # Prompt for configurable parameters
        self.max_workers = self.prompt_for_int("Enter the number of worker threads (default is 50): ", default=50)
        self.max_retries = self.prompt_for_int("Enter the maximum number of retries for rate limit errors (default is 5): ", default=5)

        # Gmail API credentials
        self.creds = None
        self.service = None

        # Processed months set
        self.processed_months = set()

    def prompt_for_confirmation(self, prompt):
        """
        Prompts the user for a yes/no confirmation.

        Args:
            prompt (str): The prompt message.

        Returns:
            bool: True if the user confirms, False otherwise.
        """
        while True:
            choice = input(prompt).strip().lower()
            if choice in ['yes', 'y']:
                return True
            elif choice in ['no', 'n']:
                return False
            else:
                print("Please enter 'yes' or 'no'.")

    def prompt_for_int(self, prompt, default):
        """
        Prompts the user for an integer value with a default.

        Args:
            prompt (str): The prompt message.
            default (int): The default value if the user inputs nothing.

        Returns:
            int: The integer value entered by the user, or the default.
        """
        while True:
            user_input = input(prompt).strip()
            if not user_input:
                return default
            try:
                value = int(user_input)
                return value
            except ValueError:
                print("Please enter a valid integer.")

    def authenticate_gmail(self):
        """
        Authenticates the user with Gmail API and initializes the service.
        """
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)
        # If there are no valid credentials, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # Initiate the OAuth flow to get new credentials with the required scopes
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for future runs
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())
        # Initialize the Gmail API service
        self.service = build("gmail", "v1", credentials=self.creds)

    def load_processed_months(self):
        """
        Loads the processed months from the log file into a set.
        """
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as log_file:
                entries = log_file.read().splitlines()
                self.processed_months.update(entries)

    def log_progress(self, year, month):
        """
        Logs the current download progress to the log file.

        Args:
            year (int): The year of the processed emails.
            month (int): The month of the processed emails.
        """
        with open(self.log_file, "a") as log_file:
            log_file.write(f"{year}/{month:02d}\n")

    def sanitize_filename(self, filename, max_length=100):
        """
        Sanitizes a string to be used as a safe filename.

        Args:
            filename (str): The original filename.
            max_length (int): The maximum length of the sanitized filename.

        Returns:
            str: A sanitized filename.
        """
        sanitized = ''.join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
        return sanitized[:max_length]

    def get_zip_file_path(self, year, month):
        """
        Returns the path of the zip file for the specified year and month.

        Args:
            year (int): The year.
            month (int): The month.

        Returns:
            str: The path to the zip file.
        """
        return os.path.join(self.save_path, str(year), f"{month:02d}.zip")

    def prepare_email_data(self, email_message, msg_id):
        """
        Extracts and structures email data for buffering.

        Args:
            email_message (email.message.EmailMessage): The email message object.
            msg_id (str): The message ID.

        Returns:
            dict: A dictionary containing structured email data.
        """
        # Extract email components
        sender = email_message.get('From', 'unknown_sender')
        subject = email_message.get('Subject', 'no_subject')
        date_str = email_message.get('Date', '')
        content_parts = []
        attachments = []

        # Sanitize sender and subject to create a safe folder name
        safe_sender = self.sanitize_filename(sender, max_length=50)
        safe_subject = self.sanitize_filename(subject, max_length=50)

        # Parse the date
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_str)
        except (TypeError, ValueError, IndexError):
            parsed_date = datetime.datetime.now()
        email_date_formatted = parsed_date.strftime('%Y%m%d_%H%M%S')

        # Generate email folder name with limited length
        email_folder_name = f"{email_date_formatted}_{safe_sender}_{msg_id}"
        if len(email_folder_name) > 100:
            # Use a hash to shorten the name
            hash_str = hashlib.md5(email_folder_name.encode()).hexdigest()
            email_folder_name = f"{email_date_formatted}_{hash_str}"

        # Extract email body and attachments
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                disposition = str(part.get('Content-Disposition') or '')
                if 'attachment' not in disposition.lower():
                    if content_type in ['text/plain', 'text/html']:
                        charset = part.get_content_charset('utf-8') or 'utf-8'
                        content = part.get_payload(decode=True).decode(charset, errors='replace')
                        content_parts.append((content_type, content))
                else:
                    attachment = self.extract_attachment(part)
                    if attachment:
                        attachments.append(attachment)
        else:
            content_type = email_message.get_content_type()
            if content_type in ['text/plain', 'text/html']:
                charset = email_message.get_content_charset('utf-8') or 'utf-8'
                content = email_message.get_payload(decode=True).decode(charset, errors='replace')
                content_parts.append((content_type, content))

        # Extract headers
        headers = {header: value for header, value in email_message.items()}

        email_data = {
            'folder_name': email_folder_name,
            'sender': sender,
            'subject': subject,
            'date_str': date_str,
            'content_parts': content_parts,
            'attachments': attachments,
            'headers': headers
        }

        return email_data

    def extract_attachment(self, part):
        """
        Extracts attachment data from an email part.

        Args:
            part (email.message.EmailMessage): The email part.

        Returns:
            dict or None: A dictionary with attachment data or None if no attachment.
        """
        filename = part.get_filename()
        if filename:
            filename = email.utils.collapse_rfc2231_value(filename)
            filename = self.sanitize_filename(filename)
            file_data = part.get_payload(decode=True)
            if file_data:
                return {'filename': filename, 'data': file_data}
            else:
                print(f"Attachment {filename} has no data or could not be decoded.")
        else:
            print("Found an attachment with no filename.")
        return None

    def write_emails_to_disk(self, email_buffer, folder_path):
        """
        Writes buffered emails to disk.

        Args:
            email_buffer (list): A list of email data dictionaries.
            folder_path (str): The path to the folder where emails will be saved.
        """
        for email_data in email_buffer:
            email_folder_path = os.path.join(folder_path, email_data['folder_name'])
            os.makedirs(email_folder_path, exist_ok=True)

            # Save email body
            for content_type, content in email_data['content_parts']:
                if content_type == 'text/plain':
                    filename = 'email.txt'
                elif content_type == 'text/html':
                    filename = 'email.html'
                else:
                    continue
                filepath = os.path.join(email_folder_path, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Save headers
            headers_filepath = os.path.join(email_folder_path, 'headers.txt')
            with open(headers_filepath, 'w', encoding='utf-8') as f:
                f.write(f"From: {email_data['sender']}\n")
                f.write(f"Date: {email_data['date_str']}\n")
                f.write(f"Subject: {email_data['subject']}\n")
                f.write("\nFull Headers:\n")
                for header, value in email_data['headers'].items():
                    f.write(f"{header}: {value}\n")

            # Save attachments
            for attachment in email_data['attachments']:
                file_path = os.path.join(email_folder_path, attachment['filename'])
                with open(file_path, 'wb') as f:
                    f.write(attachment['data'])
                print(f"Saved attachment: {file_path}")

    def process_email(self, msg_id):
        """
        Processes a single email message and returns the data.

        Args:
            msg_id (str): The message ID.

        Returns:
            dict or None: The structured email data or None if processing failed.
        """
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                # Fetch the email
                message = self.service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format='raw'  # Get the raw RFC 822 format
                ).execute()

                email_raw = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
                email_message = BytesParser(policy=policy.default).parsebytes(email_raw)

                email_data = self.prepare_email_data(email_message, msg_id)
                return email_data

            except HttpError as error:
                if error.resp.status == 429:  # Rate limit error
                    retry_count += 1
                    sleep_time = 2 ** retry_count
                    print(f"Rate limit reached while processing email ID {msg_id}, retrying after {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print(f"An error occurred while downloading email ID {msg_id}: {error}")
                    return None
            except Exception as e:
                print(f"Failed to process email ID {msg_id}: {e}")
                return None
        print(f"Exceeded maximum retries for email ID {msg_id}. Skipping.")
        return None

    def download_and_organize_emails(self, start_date_str, end_date_str):
        """
        Downloads emails within the specified date range and organizes them by year and month.

        Args:
            start_date_str (str): The start date in 'mm-dd-yyyy' format.
            end_date_str (str): The end date in 'mm-dd-yyyy' format.
        """
        start_date = datetime.datetime.strptime(start_date_str, "%m-%d-%Y")
        end_date = datetime.datetime.strptime(end_date_str, "%m-%d-%Y")
        if start_date > end_date:
            print("Start date must be earlier than or equal to end date.")
            return

        try:
            # Generate all months within the date range
            months = []
            current_date = datetime.datetime(start_date.year, start_date.month, 1)
            while current_date <= end_date:
                months.append((current_date.year, current_date.month))
                # Move to the first day of the next month
                if current_date.month == 12:
                    current_date = datetime.datetime(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime.datetime(current_date.year, current_date.month + 1, 1)

            for year, month in months:
                year_month_key = f"{year}/{month:02d}"
                if year_month_key in self.processed_months:
                    print(f"Skipping {year}/{month:02d} as it is already processed.")
                    continue

                zipfile_path = self.get_zip_file_path(year, month)
                if os.path.exists(zipfile_path):
                    print(f"Skipping {year}/{month:02d} as it is already compressed.")
                    self.log_progress(year, month)
                    continue

                month_start = datetime.datetime(year, month, 1)
                if month == 12:
                    next_month = datetime.datetime(year + 1, 1, 1)
                else:
                    next_month = datetime.datetime(year, month + 1, 1)

                # Adjust month start and end dates based on user-specified date range
                actual_start = max(month_start, start_date)
                actual_end = min(next_month - datetime.timedelta(days=1), end_date) + datetime.timedelta(days=1)

                # Build date range query
                after_date_str = actual_start.strftime('%Y/%m/%d')
                before_date_str = actual_end.strftime('%Y/%m/%d')

                # Exclude spam and trash
                query = f"after:{after_date_str} before:{before_date_str} -in:spam -in:trash"

                print(f"Processing emails for {year}/{month:02d}")

                folder_path = os.path.join(self.save_path, str(year), f"{month:02d}")
                # Delete the folder if it exists
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)

                page_token = None
                all_message_ids = []

                while True:
                    try:
                        # Fetch emails with pagination
                        results = self.service.users().messages().list(
                            userId="me",
                            q=query,
                            pageToken=page_token,
                            maxResults=1000  # Adjust batch size as needed
                        ).execute()
                        messages = results.get("messages", [])

                        if not messages:
                            if not page_token:
                                print(f"No messages found for {year}/{month:02d}.")
                            break

                        # Collect message IDs
                        all_message_ids.extend([msg["id"] for msg in messages])

                        page_token = results.get("nextPageToken")
                        if not page_token:
                            break  # Exit the loop if there are no more pages

                    except HttpError as error:
                        print(f"An error occurred: {error}")
                        if error.resp.status == 429:
                            print("Rate limit reached, waiting before retrying...")
                            time.sleep(10)
                            continue

                if all_message_ids:
                    # Create folder for the month
                    os.makedirs(folder_path, exist_ok=True)

                    # Multithreaded fetching and processing
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = [executor.submit(self.process_email, msg_id) for msg_id in all_message_ids]
                        email_buffer = []
                        buffer_limit = 100  # Adjust as needed

                        for future in as_completed(futures):
                            email_data = future.result()
                            if email_data:
                                email_buffer.append(email_data)
                                print(f"Processed email: {email_data['folder_name']}")
                            else:
                                print("Failed to process an email.")

                            if len(email_buffer) >= buffer_limit:
                                self.write_emails_to_disk(email_buffer, folder_path)
                                email_buffer.clear()

                        # Write any remaining emails in the buffer
                        if email_buffer:
                            self.write_emails_to_disk(email_buffer, folder_path)
                            email_buffer.clear()

                    # Compress the month's folder and remove uncompressed data
                    self.compress_month_folder(year, month)
                    # Log progress for the month
                    self.log_progress(year, month)
                else:
                    # If no emails were downloaded, ensure no empty directories are left
                    if os.path.exists(folder_path):
                        os.rmdir(folder_path)
                    print(f"No emails downloaded for {year}/{month:02d}, skipping compression and logging.")

                # Delete emails after archiving if the user opted for it
                if self.delete_after_archive:
                    self.delete_emails_in_range(after_date_str, before_date_str)

        except HttpError as error:
            print(f"An error occurred: {error}")

    def compress_month_folder(self, year, month):
        """
        Compresses the month's folder to save space.

        Args:
            year (int): The year.
            month (int): The month.
        """
        folder_path = os.path.join(self.save_path, str(year), f"{month:02d}")
        if os.path.exists(folder_path):
            shutil.make_archive(folder_path, 'zip', folder_path)
            shutil.rmtree(folder_path)
            print(f"Compressed and removed folder: {folder_path}")

    def delete_emails_in_range(self, after_date_str, before_date_str):
        """
        Deletes emails within the specified date range.

        Args:
            after_date_str (str): The start date in 'YYYY/MM/DD' format.
            before_date_str (str): The end date in 'YYYY/MM/DD' format.
        """
        try:
            # Build the date range query for deletion
            query = f"after:{after_date_str} before:{before_date_str} -in:spam -in:trash"
            page_token = None

            while True:
                results = self.service.users().messages().list(
                    userId="me",
                    q=query,
                    pageToken=page_token,
                    maxResults=1000  # Adjust batch size as needed
                ).execute()
                messages = results.get("messages", [])

                if not messages:
                    print(f"No more emails to delete between {after_date_str} and {before_date_str}.")
                    break

                message_ids = [msg["id"] for msg in messages]

                # Batch delete messages
                batch_request = {'ids': message_ids}
                try:
                    self.service.users().messages().batchDelete(userId="me", body=batch_request).execute()
                    print(f"Deleted {len(message_ids)} emails.")
                except HttpError as error:
                    print(f"An error occurred while deleting emails: {error}")
                    if error.resp.status == 429:
                        print("Rate limit reached, waiting before retrying...")
                        time.sleep(10)
                        continue

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

        except HttpError as error:
            print(f"An error occurred: {error}")

    def run(self):
        """
        Runs the Gmail archiver.
        """
        # Prompt user for start and end dates
        start_date_str = input("Enter the start date (mm-dd-yyyy): ").strip()
        end_date_str = input("Enter the end date (mm-dd-yyyy): ").strip()
        try:
            datetime.datetime.strptime(start_date_str, "%m-%d-%Y")
            datetime.datetime.strptime(end_date_str, "%m-%d-%Y")
        except ValueError:
            print("Incorrect date format. Please enter the date in mm-dd-yyyy format.")
            return

        # Authenticate and initialize the Gmail API service
        self.authenticate_gmail()

        # Load processed months from log file
        self.load_processed_months()

        # Download and organize emails, and optionally delete them
        self.download_and_organize_emails(start_date_str, end_date_str)

if __name__ == "__main__":
    """
    Sample usage:
    -------------
    1. Ensure you have 'credentials.json' in the same directory as this script.
       This file is obtained from the Google Cloud Console after enabling the Gmail API.

    2. Run the script:
       python gmail_archiver.py

    3. Follow the prompts:
       - Confirm whether to delete emails after archiving.
       - Enter the base path for archiving.
       - Enter the start and end dates in 'mm-dd-yyyy' format.
       - Optionally adjust the number of worker threads and maximum retries.

    4. The script will archive your emails within the specified date range,
       organize them by year and month, compress them, and
       optionally delete them from your Gmail account.
    """
    archiver = GmailArchiver()
    archiver.run()