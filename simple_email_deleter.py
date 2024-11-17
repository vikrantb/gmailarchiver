import hashlib
import os
import datetime
import time
import base64
import email
import shutil
import argparse
from email import policy
from email.parser import BytesParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://mail.google.com/"]
MAX_WORKERS = 10
MAX_RETRIES = 5
total_emails = 0
emails_downloaded = 0
emails_deleted = 0
attachments_saved = 0
space_saved = 0
zip_files_created = 0
original_size = 0

def authenticate_gmail():
    """Authenticates the user and returns the credentials."""
    if os.path.exists("token.json"):
        os.remove("token.json")  # Ensure a fresh token for each run
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def sanitize_filename(filename, max_length=100):
    """Sanitizes a string to be used as a safe filename."""
    sanitized = ''.join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
    return sanitized[:max_length]


def summarize_statistics(start_date, end_date, base_path, query, label, delete, total_emails, emails_downloaded, emails_deleted, attachments_saved, original_size,
                         space_saved, zip_files_created):
    """
    Summarizes and prints statistics about the Gmail archiving process.

    Args:
        start_date (str): The start date of the email retrieval in mm-dd-yyyy format.
        end_date (str): The end date of the email retrieval in mm-dd-yyyy format.
        base_path (str): Base path where emails are archived.
        query (str): Custom Gmail search query.
        label (str): Gmail label to filter emails.
        delete (bool): Whether emails were deleted after archiving.
        total_emails (int): Total number of emails retrieved from Gmail.
        emails_downloaded (int): Number of emails successfully downloaded.
        emails_deleted (int): Number of emails deleted (if deletion was enabled).
        attachments_saved (int): Total number of attachments saved.
        original_size (float): Original total size of the emails in bytes before compression.
        space_saved (float): Total disk space saved in bytes due to compression.
        zip_files_created (int): Number of zip files created during compression.
    """
    def format_size(size_in_bytes):
        """Converts bytes to a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} PB"

    # Prepare formatted sizes
    original_size_formatted = format_size(original_size)
    space_saved_formatted = format_size(space_saved)

    # Build the filter description
    filters = []
    if start_date and end_date:
        filters.append(f"from **{start_date}** to **{end_date}**")
    elif start_date:
        filters.append(f"starting from **{start_date}**")
    elif end_date:
        filters.append(f"up to **{end_date}**")
    if label:
        filters.append(f"label: **'{label}'**")
    if query:
        filters.append(f"query: **'{query}'**")
    filter_summary = ", ".join(filters) if filters else "**all emails**"

    # Determine the action type
    if delete:
        action_type = (
            f"📤 **Archived and deleted** **{emails_deleted}** emails, saving 💾 **{space_saved_formatted}** of disk space."
        )
    else:
        action_type = (
            f"📤 **Archived** **{emails_downloaded}** emails with 📎 **{attachments_saved} attachments**. "
            f"⚠️ While emails were not deleted, this could have saved 💾 **{space_saved_formatted}**."
        )

    # Build the compression summary
    compression_summary = f"📦 **Compression Complete**: Created **{zip_files_created}** zip files, shrinking emails from **{original_size_formatted}**."

    # Construct the final message
    final_message = (
        f"\n✨ **Gmail Archiving Summary** ✨\n\n"
        f"🔍 **Filters Applied**: {filter_summary}\n"
        f"📧 **Emails Processed**: **{total_emails}**\n"
        f"{action_type}\n"
        f"📂 **Data Stored At**: {base_path}\n"
        f"{compression_summary}\n\n"
        f"🔒 Your emails are now securely archived, beautifully organized, and ready for future use! 🚀\n"
    )

    # Add ASCII art representing a secure archive
    ascii_art = """
          ________________________
         |########################|
         |#  ________________   #|
         |# |                |  #|
         |# | Archiving Safe |  #|
         |# |________________|  #|
         |########################|
         |########################|
         |########################|
         |########################|
         |########################|
         \\########################/
          \\______________________/
    📨 Mission accomplished! Your data is securely saved and organized! 📂
    """

    # Combine message and ASCII art
    print(final_message)
    print(ascii_art)


def prepare_email_data(email_message, msg_id):
    """Extracts and structures email data for buffering."""
    sender = email_message.get('From', 'unknown_sender')
    subject = email_message.get('Subject', 'no_subject')
    date_str = email_message.get('Date', '')
    content_parts = []
    attachments = []

    safe_sender = sanitize_filename(sender, max_length=50)
    safe_subject = sanitize_filename(subject, max_length=50)

    try:
        parsed_date = email.utils.parsedate_to_datetime(date_str)
    except (TypeError, ValueError, IndexError):
        parsed_date = datetime.datetime.now()
    email_date_formatted = parsed_date.strftime('%Y%m%d_%H%M%S')

    email_folder_name = f"{email_date_formatted}_{safe_sender}_{msg_id}"
    if len(email_folder_name) > 100:
        hash_str = hashlib.md5(email_folder_name.encode()).hexdigest()
        email_folder_name = f"{email_date_formatted}_{hash_str}"

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
                attachment = extract_attachment(part)
                if attachment:
                    attachments.append(attachment)
    else:
        content_type = email_message.get_content_type()
        if content_type in ['text/plain', 'text/html']:
            charset = email_message.get_content_charset('utf-8') or 'utf-8'
            content = email_message.get_payload(decode=True).decode(charset, errors='replace')
            content_parts.append((content_type, content))

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


def extract_attachment(part):
    """Extracts attachment data from an email part."""
    filename = part.get_filename()
    if filename:
        filename = email.utils.collapse_rfc2231_value(filename)
        filename = sanitize_filename(filename)
        file_data = part.get_payload(decode=True)
        if file_data:
            return {'filename': filename, 'data': file_data}
    return None


def write_buffer_to_disk(email_buffer, folder_path):
    """Writes buffered emails to disk organized by year/month."""
    global attachments_saved
    for email_data in email_buffer:
        try:
            # Extract year and month from email's date
            date_str = email_data.get('date_str', '')
            parsed_date = email.utils.parsedate_to_datetime(date_str)
            year = parsed_date.strftime('%Y')
            month = parsed_date.strftime('%m')

            # Construct the year/month folder path
            year_month_path = os.path.join(folder_path, year, month)
            os.makedirs(year_month_path, exist_ok=True)  # Create year/month folder if it doesn't exist

            # Create the email-specific folder
            email_folder_path = os.path.join(year_month_path, email_data['folder_name'])
            os.makedirs(email_folder_path, exist_ok=True)

            # Save email content
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
                for header, value in email_data['headers'].items():
                    f.write(f"{header}: {value}\n")

            # Save attachments
            for attachment in email_data['attachments']:
                attachments_saved += 1
                file_path = os.path.join(email_folder_path, attachment['filename'])
                with open(file_path, 'wb') as f:
                    f.write(attachment['data'])

        except Exception as e:
            print(f"Error writing email data to disk for {email_data['folder_name']}: {e}")


def compress_month_folder(folder_path):
    """Compresses each month-level folder."""
    global space_saved, zip_files_created, original_size  # Declare as global to modify these variables

    for root, dirs, _ in os.walk(folder_path):
        for dir_name in dirs:
            month_folder = os.path.join(root, dir_name)
            if not os.path.isdir(month_folder):
                continue
            folder_size_before = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(month_folder)
                for filename in filenames
            )
            shutil.make_archive(month_folder, 'zip', month_folder)
            zip_files_created += 1  # Increment the global counter
            shutil.rmtree(month_folder)
            zip_size = os.path.getsize(f"{month_folder}.zip")
            original_size += folder_size_before  # Increment the global counter
            space_saved += folder_size_before - zip_size  # Increment the global space saved


def process_email(creds, msg_id):
    """Processes a single email message."""
    global emails_downloaded
    global emails_deleted

    service = build("gmail", "v1", credentials=creds)
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            message = service.users().messages().get(userId="me", id=msg_id, format='raw').execute()
            email_raw = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
            email_message = BytesParser(policy=policy.default).parsebytes(email_raw)
            return prepare_email_data(email_message, msg_id)
        except HttpError as error:
            if error.resp.status == 429:
                retry_count += 1
                time.sleep(2 ** retry_count)
            else:
                print(f"Error processing email ID {msg_id}: {error}")
                return None
        except Exception as e:
            print(f"Failed to process email ID {msg_id}: {e}")
            return None


def build_query(args):
    """Builds the Gmail search query."""
    query = args.query
    if args.start_date:
        start_date = datetime.datetime.strptime(args.start_date, "%m-%d-%Y").strftime('%Y/%m/%d')
        query += f" after:{start_date}"
    if args.end_date:
        end_date = datetime.datetime.strptime(args.end_date, "%m-%d-%Y").strftime('%Y/%m/%d')
        query += f" before:{end_date}"
    if args.label:
        query += f" label:{args.label}"
    query += " -in:spam -in:trash"
    return query.strip()


def get_message_ids(creds, query):
    """Fetches email message IDs based on the query."""
    global total_emails
    service = build("gmail", "v1", credentials=creds)
    message_ids = []
    page_token = None

    while True:
        try:
            results = service.users().messages().list(userId="me", q=query, pageToken=page_token, maxResults=500).execute()
            messages = results.get("messages", [])
            if not messages:
                break
            message_ids.extend([msg["id"] for msg in messages])
            page_token = results.get("nextPageToken")
            if not page_token:
                break
        except HttpError as error:
            if error.resp.status == 429:
                time.sleep(10)
                continue
            else:
                print(f"HttpError while listing messages: {error}")
                break
        except Exception as e:
            print(f"Unexpected error while listing messages: {e}")
            break
    total_emails = len(message_ids)
    return message_ids

def delete_emails(creds, message_ids):
    """
    Deletes emails based on their message IDs.

    Args:
        creds: Authenticated Gmail API credentials.
        message_ids (list): List of email message IDs to delete.

    Returns:
        int: Number of emails successfully deleted.
    """
    service = build("gmail", "v1", credentials=creds)
    deleted_count = 0

    try:
        for i in range(0, len(message_ids), 1000):  # Gmail allows batch deletion of up to 1000 emails at a time
            batch = message_ids[i:i + 1000]
            service.users().messages().batchDelete(userId="me", body={"ids": batch}).execute()
            deleted_count += len(batch)
            print(f"Deleted {len(batch)} emails.")
    except HttpError as error:
        print(f"Error during email deletion: {error}")
    except Exception as e:
        print(f"Unexpected error during email deletion: {e}")

    return deleted_count

def archive_emails(args):
    """Archives emails based on arguments."""
    creds = authenticate_gmail()
    query = build_query(args)
    message_ids = get_message_ids(creds, query)

    folder_path = os.path.expanduser(args.base_path)
    os.makedirs(folder_path, exist_ok=True)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_email, creds, msg_id) for msg_id in message_ids]
        email_buffer = []

        for future in as_completed(futures):
            email_data = future.result()
            if email_data:
                email_buffer.append(email_data)
            if len(email_buffer) >= 50:
                write_buffer_to_disk(email_buffer, folder_path)
                email_buffer.clear()

        if email_buffer:
            write_buffer_to_disk(email_buffer, folder_path)

    compress_month_folder(folder_path)

    # Add email deletion logic if the `--delete` flag is passed
    if getattr(args, "delete", False):
        emails_deleted = delete_emails(creds, message_ids)

    # Update call to include the additional arguments
    summarize_statistics(
        start_date=args.start_date,
        end_date=args.end_date,
        base_path=args.base_path,
        query=args.query,
        label=args.label,
        delete=args.delete,
        total_emails=total_emails,
        emails_downloaded=emails_downloaded,
        emails_deleted=emails_deleted if args.delete else -1,
        attachments_saved=attachments_saved,
        original_size=space_saved + original_size,  # Update based on tracked sizes
        space_saved=space_saved,
        zip_files_created=zip_files_created
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gmail Archiver")
    parser.add_argument("--start-date", type=str, required=True, help="Start date in mm-dd-yyyy format.")
    parser.add_argument("--end-date", type=str, required=True, help="End date in mm-dd-yyyy format.")
    parser.add_argument("--base-path", type=str, default=os.getcwd(), help="Base path for saving emails.")
    parser.add_argument("--query", type=str, default="", help="Custom Gmail search query (e.g., 'is:starred').")
    parser.add_argument("--label", type=str, help="Gmail label to filter emails (e.g., 'INBOX').")
    parser.add_argument("--delete", action="store_true", help="Delete emails after archiving.")

    args = parser.parse_args()
    archive_emails(args)