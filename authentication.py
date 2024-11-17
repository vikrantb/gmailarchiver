import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from constants import SCOPES


def authenticate_gmail():
    """
    Authenticates the user and returns the credentials.

    This function handles the authentication process for accessing Gmail API.
    It checks for existing credentials in 'token.json', refreshes them if expired,
    or initiates a new authentication flow if no valid credentials are found.

    Returns:
        google.oauth2.credentials.Credentials: The authenticated credentials.
    """
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
