import os
import datetime
import time
import base64
import email
import shutil
from email import policy
from email.parser import BytesParser
import hashlib
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://mail.google.com/"]
MAX_WORKERS = 10
MAX_RETRIES = 5


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
    """Writes buffered emails to disk."""
    for email_data in email_buffer:
        email_folder_path = os.path.join(folder_path, email_data['folder_name'])
        os.makedirs(email_folder_path, exist_ok=True)

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

        headers_filepath = os.path.join(email_folder_path, 'headers.txt')
        with open(headers_filepath, 'w', encoding='utf-8') as f:
            f.write(f"From: {email_data['sender']}\n")
            f.write(f"Date: {email_data['date_str']}\n")
            f.write(f"Subject: {email_data['subject']}\n")
            for header, value in email_data['headers'].items():
                f.write(f"{header}: {value}\n")

        for attachment in email_data['attachments']:
            file_path = os.path.join(email_folder_path, attachment['filename'])
            with open(file_path, 'wb') as f:
                f.write(attachment['data'])


def process_email(creds, msg_id):
    """Processes a single email message."""
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


def download_emails(creds, query):
    """Downloads emails based on the query."""
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
                print("Rate limit exceeded. Retrying in 10 seconds...")
                time.sleep(10)
                continue
            else:
                print(f"HttpError while listing messages: {error}")
                break
        except Exception as e:
            print(f"Unexpected error while listing messages: {e}")
            break
    return message_ids


def delete_emails(creds, message_ids):
    """Deletes emails by their message IDs."""
    service = build("gmail", "v1", credentials=creds)
    try:
        for i in range(0, len(message_ids), 1000):
            batch = message_ids[i:i + 1000]
            service.users().messages().batchDelete(userId="me", body={"ids": batch}).execute()
            print(f"Deleted {len(batch)} emails.")
    except HttpError as error:
        print(f"Error during email deletion: {error}")
    except Exception as e:
        print(f"Unexpected error during email deletion: {e}")


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


def archive_emails(args):
    """Archives emails based on arguments."""
    creds = authenticate_gmail()
    query = build_query(args)
    message_ids = download_emails(creds, query)

    folder_path = os.path.join(args.base_path, "emails")
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

    if args.delete:
        print("Deleting emails after archiving...")
        delete_emails(creds, message_ids)


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