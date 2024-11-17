import datetime
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def build_query(args):
    """
    Builds the Gmail search query based on the provided arguments.

    Args:
        args (argparse.Namespace): The command-line arguments containing query parameters.

    Returns:
        str: The constructed Gmail search query.
    """
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
    """
    Fetches email message IDs based on the provided query.

    Args:
        creds (google.oauth2.credentials.Credentials): The credentials for accessing the Gmail API.
        query (str): The Gmail search query.

    Returns:
        list: A list of email message IDs that match the query.
    """
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
