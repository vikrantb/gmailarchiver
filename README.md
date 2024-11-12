# Gmail Archiver

Gmail Archiver is a tool to archive your Gmail emails within a specified date range. It backs up emails to local storage, organizes them by year and month, compresses them, and optionally deletes them from your Gmail account.

## Features

- Archive emails within a specified date range.
- Organize emails by year and month.
- Compress emails into ZIP files.
- Optionally delete emails from Gmail after archiving.
- Multithreaded processing for efficient archiving.

## Requirements

- Python 3.7 or higher
- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/gmailarchiver.git
   cd gmailarchiver