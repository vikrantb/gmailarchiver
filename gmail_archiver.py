import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from authentication import authenticate_gmail
from constants import MAX_WORKERS, total_emails, emails_downloaded, attachments_saved, space_saved, zip_files_created, \
    original_size
from email_deleter import delete_emails
from email_processor import process_email
from persistence_handler import write_buffer_to_disk, compress_month_folder
from query_processor import build_query, get_message_ids
from status_summarizer import summarize_statistics


def archive_emails(args):
    """
    Archives emails based on arguments.

    Args:
        args (argparse.Namespace): The command-line arguments.

    Returns:
        None
    """
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

    space_saved, zip_files_created, original_size = compress_month_folder(folder_path)

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