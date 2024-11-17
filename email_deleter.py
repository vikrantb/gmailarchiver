from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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
