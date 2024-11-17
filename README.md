
# Gmail Archiver

The **Gmail Archiver** tool is a Python utility designed for downloading and archiving emails from a specified Gmail account. This tool organizes emails by year and month, compresses them into `.zip` files for each month, and optionally deletes archived emails from the Gmail account to manage inbox space.

---

## Features

- **Download and Archive Emails**: Downloads emails before a specified cutoff date, organizing them by year and month.
- **Automatic Compression**: Archives are saved in `.zip` format, structured as `year/month.zip`.
- **Inbox Management**: Optionally delete emails from Gmail after archiving.
- **Configurable Parameters**: Allows setting parameters like the archive path, cutoff date, and maximum parallelization for efficient downloading.
- **Multi-threaded Execution**: Supports configurable parallelization to speed up the email download process.

---

## Requirements

- Python 3.7+
- Google API Client Library for Python (`google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`)

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vikrantb/gmailarchiver.git
   cd gmail_archiver
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 3. **Set up Google API Credentials**

#### Create a Google Cloud Project

1. Go to the [Google Cloud Console Project Creation page](https://console.cloud.google.com/projectcreate).
2. If you already have a project, skip to **Step 3.3**. Otherwise, create a new project by:
   - Entering a **Project Name**.
   - Selecting **No organization** (if applicable).
3. Click **Create** to finish creating your project.

#### Enable the Gmail API for Your Project

1. Navigate to the **Enable API and Services** page for the Gmail API by clicking [here](https://console.cloud.google.com/apis/enableflow?apiid=gmail.googleapis.com).
2. Ensure the correct project is selected in the top navigation bar.
3. Click **Enable** to activate the Gmail API for your project.

#### Set Up OAuth Consent

1. Go to the [OAuth consent screen setup](https://console.cloud.google.com/apis/credentials/consent) for your project.
2. If no app exists, create one by entering the necessary details, such as your app name and email.
3. Ensure the following **OAuth Scopes** are listed and have access:
   - **Gmail API**: `https://mail.google.com/` - Read, compose, send, and permanently delete all your email from Gmail.
   - **Gmail API**: `https://www.googleapis.com/auth/gmail.modify` - Read, compose, and send emails from your Gmail account.
4. If you are just using the app for yourself (not for public use), set the **Publishing Status** of the app to **Testing** on the first screen. For broader access, you'll need to submit the app for verification, which may take up to a day.

#### Create OAuth 2.0 Credentials

1. Go to the [API Credentials page](https://console.cloud.google.com/apis/credentials) in Google Cloud Console.
2. Select your project from the drop-down menu if it’s not already selected.
3. If there are no existing credentials, create new ones:
   - Click **Create Credentials** and select **OAuth client ID**.
   - For **Application type**, choose **Desktop app**.
   - Name your credentials (e.g., "Gmail Archiver Credentials") and click **Create**.
4. A dialog will appear with the **OAuth Client ID**. Click **Download JSON** to save the `credentials.json` file.

#### Save the Credentials File

1. Download the `credentials.json` file to your local machine.
2. Move the downloaded file to the directory where the Gmail Archiver script is located (e.g., `gmail_archiver/`).
3. Rename the file to `credentials.json`.

#### Verify Setup

1. Open your terminal or command prompt and run the Gmail Archiver script.
2. During the first run, the script will prompt you to authenticate. Follow the on-screen instructions to complete the OAuth authentication.

> **Note**: Keep `credentials.json` secure, as it contains sensitive information. Never share this file or check it into source control.

---

## Usage

### Running the Archiver Tool

Run the `gmail_archiver.py` script with the following command:

```bash
python gmail_archiver.py
```

Upon running, the tool will prompt you for the following information:

1. **Base Path for Archive**: The path where the emails will be saved. If not specified, it defaults to `./gmail_archives`.
2. **Cutoff Date**: Specify the cutoff date (in `MM-DD-YYYY` format) to download emails older than this date.
3. **Delete Emails After Archiving**: Confirm if you'd like to delete the emails from Gmail after archiving. Type "yes" to confirm.



### Examples

**Example 1: Basic Archiving**  
**Scenario:** You want to keep a copy of all your emails for future reference, but you’re not ready to delete anything yet.  
**Use:**  
`python gmail_archiver.py --base-path ./gmail_archives`  
**What it does:** Archives all emails in your account to the ./gmail_archives directory, organizing them by year and month. No emails will be deleted, and you’ll have a clean backup for safekeeping.

**Example 2: Goodbye, GmailArchiver Corp!**  
**Scenario:** You just left your job at GmailArchiver Corp, and all their emails are labeled GmailArchiver. Time to clean up your inbox!  
**Use:**  
`python gmail_archiver.py --label GmailArchiver --delete --base-path ./gmail_archives`  
**What it does:** Archives all emails tagged with the GmailArchiver label, saves them locally, and deletes them from Gmail. Say goodbye to clutter and hello to a fresh start!

**Example 3: Remember 2022**  
**Scenario:** You want to archive emails from a specific date range, like all the correspondence from the eventful year of 2022.  
**Use:**  
`python gmail_archiver.py --start-date 01-01-2022 --end-date 12-31-2022 --base-path ./gmail_archives_2022`  
**What it does:** Archives all emails received between January 1, 2022, and December 31, 2022, into ./gmail_archives_2022. No emails are deleted, so you can relive those memories anytime!

**Example 4: Invoice Hunters**  
**Scenario:** You’ve been searching for invoices scattered across your inbox. Time to organize them all in one place.  
**Use:**  
`python gmail_archiver.py --query "invoice" --base-path ./invoice_archives`  
**What it does:** Finds all emails with the word “invoice” and archives them into the ./invoice_archives folder. Your financial trail is now neatly saved!

**Example 5: Work and Meetings**  
**Scenario:** You need to archive emails labeled Work that also contain the word “meeting.” Perfect for keeping your professional life organized.  
**Use:**  
`python gmail_archiver.py --label Work --query "meeting" --base-path ./work_meeting_archives`  
**What it does:** Archives all work-related meeting emails, combining label and query filters, and saves them in ./work_meeting_archives.

**Example 6: Out with the Old**  
**Scenario:** Time to declutter! Archive and delete all emails you received before 2021.  
**Use:**  
`python gmail_archiver.py --end-date 12-31-2020 --delete --base-path ./old_emails`  
**What it does:** Archives emails up to December 31, 2020, stores them in ./old_emails, and deletes them from Gmail. Clean slate, anyone?

**Example 7: Starting Fresh**  
**Scenario:** You’re only interested in recent emails. Archive everything from January 1, 2023, onward.  
**Use:**  
`python gmail_archiver.py --start-date 01-01-2023 --base-path ./recent_emails`  
**What it does:** Archives emails received from January 1, 2023, onward into the ./recent_emails folder. No old baggage here! You still might want to delete older emails.

**Example 8: Keep archiving important stuff**  
**Scenario:** Your starred emails are important! Archive them for safekeeping.  
**Use:**  
`python gmail_archiver.py --label STARRED --base-path ./starred_archives`  
**What it does:** Archives all starred emails to ./starred_archives. Your top-priority emails are now securely saved.

**Example 9: The Exit Strategy**  
**Scenario:** You’re leaving your job and want to archive all emails labeled Work before deleting them.  
**Use:**  
`python gmail_archiver.py --label Work --base-path ./job_backup --delete`  
**What it does:** Archives emails labeled Work, stores them in ./job_backup, and deletes them from Gmail. A tidy way to exit!

**Example 10: Big Attachments, Big Savings**  
**Scenario:** Your Gmail is running out of space! Archive emails with attachments larger than 10 MB.  
**Use:**  
`python gmail_archiver.py --query "size:10485760" --base-path ./large_attachments`  
**What it does:** Finds all emails with attachments larger than 10 MB, archives them into ./large_attachments, and retains them in Gmail.

**Example 11: Project Skunk works**  
**Scenario:** You’re working on a project named “Skunk works” and need all related emails labeled Work, starting from January 1, 2022, and mentioning “Skunk works”.  
**Use:**  
`python gmail_archiver.py --start-date 01-01-2022 --label Work --query "Skunk works" --base-path ./project_emails`  
**What it does:** Archives all emails labeled Work, received after January 1, 2022, and containing “Skunk works,” into ./project_emails.

**Example 12: Full Backup Mode**  
**Scenario:** No filters, no queries. You want to back up everything, everywhere, all at once.  
**Use:**  
`python gmail_archiver.py --base-path ./all_emails`  
**What it does:** Archives all emails in your Gmail account into ./all_emails. No emails are deleted, and no filter is applied — just a clean, comprehensive backup.
