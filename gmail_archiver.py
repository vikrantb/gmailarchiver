from authentication import authenticate_gmail
from email_utils import sanitize_filename, write_emails_to_disk, compress_folder
import os
import datetime
import base64
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from email import policy
from email.parser import BytesParser

class GmailArchiver:
    SCOPES = ["https://mail.google.com/"]

    def __init__(self, args):
        self.delete_after_archive = args.delete
        self.base_path = args.base_path
        self.start_date_str = args.start_date
        self.end_date_str = args.end_date
        self.custom_query = args.query
        self.max_workers = args.threads
        self.service = authenticate_gmail(self.SCOPES)

    def build_query(self):
        query = self.custom_query if self.custom_query else ""
        if self.start_date_str:
            start_date = datetime.datetime.strptime(self.start_date_str, "%m-%d-%Y")
            query += f" after:{start_date.strftime('%Y/%m/%d')}"
        if self.end_date_str:
            end_date = datetime.datetime.strptime(self.end_date_str, "%m-%d-%Y")
            query += f" before:{(end_date + datetime.timedelta(days=1)).strftime('%Y/%m/%d')}"
        query += " -in:spam -in:trash"
        return query.strip()

    def download_emails(self, query):
        all_message_ids = []
        page_token = None

        while True:
            results = self.service.users().messages().list(userId="me", q=query, pageToken=page_token, maxResults=1000).execute()
            messages = results.get("messages", [])
            if not messages:
                break
            all_message_ids.extend(msg["id"] for msg in messages)
            page_token = results.get("nextPageToken")
            if not page_token:
                break

        return all_message_ids

    def process_emails(self, message_ids, folder_path):
        os.makedirs(folder_path, exist_ok=True)
        email_buffer = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.fetch_email, msg_id) for msg_id in message_ids]
            for future in as_completed(futures):
                email_data = future.result()
                if email_data:
                    email_buffer.append(email_data)
        write_emails_to_disk(email_buffer, folder_path)

    def fetch_email(self, msg_id):
        try:
            message = self.service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
            email_raw = base64.urlsafe_b64decode(message["raw"].encode("ASCII"))
            email_message = BytesParser(policy=policy.default).parsebytes(email_raw)

            # Extract email components
            sender = email_message.get("From", "unknown_sender")
            subject = email_message.get("Subject", "no_subject")
            date_str = email_message.get("Date", "")
            content_parts = []
            attachments = []

            # Extract body and attachments
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    if content_type in ["text/plain", "text/html"]:
                        charset = part.get_content_charset("utf-8") or "utf-8"
                        content = part.get_payload(decode=True).decode(charset, errors="replace")
                        content_parts.append((content_type, content))
                    elif part.get("Content-Disposition") and "attachment" in part.get("Content-Disposition").lower():
                        attachments.append(self.extract_attachment(part))
            else:
                content_type = email_message.get_content_type()
                if content_type in ["text/plain", "text/html"]:
                    charset = email_message.get_content_charset("utf-8") or "utf-8"
                    content = email_message.get_payload(decode=True).decode(charset, errors="replace")
                    content_parts.append((content_type, content))

            # Prepare email data
            return {
                "sender": sender,
                "subject": subject,
                "date": date_str,
                "content": content_parts,
                "attachments": attachments,
            }
        except Exception as e:
            print(f"Failed to process email {msg_id}: {e}")
            return None

    def extract_attachment(self, part):
        filename = part.get_filename()
        if filename:
            file_data = part.get_payload(decode=True)
            return {"filename": sanitize_filename(filename), "data": file_data}
        return None
    def archive_emails(self):
        query = self.build_query()
        message_ids = self.download_emails(query)
        folder_path = os.path.join(self.base_path, "emails")
        self.process_emails(message_ids, folder_path)
        compress_folder(folder_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gmail Archiver Tool")
    parser.add_argument('--delete', action='store_true', help='Delete emails after archiving.')
    parser.add_argument('--base-path', type=str, default=os.getcwd(), help='Base path for archiving.')
    parser.add_argument('--start-date', type=str, help='Start date in mm-dd-yyyy format.')
    parser.add_argument('--end-date', type=str, help='End date in mm-dd-yyyy format.')
    parser.add_argument('--query', type=str, help='Custom Gmail search query.')
    parser.add_argument('--threads', type=int, default=10, help='Number of worker threads.')

    args = parser.parse_args()
    archiver = GmailArchiver(args)
    archiver.archive_emails()