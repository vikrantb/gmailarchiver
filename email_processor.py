import base64
import datetime
import email
import hashlib
import time
from email import policy
from email.parser import BytesParser

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from constants import MAX_RETRIES


def sanitize_filename(filename, max_length=100):
    """
    Sanitizes a string to be used as a safe filename.

    Args:
        filename (str): The original filename.
        max_length (int): The maximum length of the sanitized filename.

    Returns:
        str: The sanitized filename.
    """
    sanitized = ''.join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
    return sanitized[:max_length]


def prepare_email_data(email_message, msg_id):
    """
    Extracts and structures email data for buffering.

    Args:
        email_message (email.message.EmailMessage): The email message object.
        msg_id (str): The message ID of the email.

    Returns:
        dict: A dictionary containing structured email data.
    """
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
    """
    Extracts attachment data from an email part.

    Args:
        part (email.message.EmailMessage): The email part containing the attachment.

    Returns:
        dict: A dictionary containing the filename and data of the attachment, or None if no attachment is found.
    """
    filename = part.get_filename()
    if filename:
        filename = email.utils.collapse_rfc2231_value(filename)
        filename = sanitize_filename(filename)
        file_data = part.get_payload(decode=True)
        if file_data:
            return {'filename': filename, 'data': file_data}
    return None


def process_email(creds, msg_id):
    """
    Processes a single email message.

    Args:
        creds (google.oauth2.credentials.Credentials): The credentials for accessing the Gmail API.
        msg_id (str): The message ID of the email.

    Returns:
        dict: A dictionary containing structured email data, or None if processing fails.
    """
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
