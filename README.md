
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

Below are several scenarios showcasing different use cases of the Gmail Archiver tool:

---

#### **Example 1: Basic Archiving**
You want to archive all your emails from the start of time to the present without deleting them from Gmail. 

```bash
python gmail_archiver.py --base-path ./gmail_archives
```

**What it does?**  
This command will archive all emails in your account to the `./gmail_archives` directory, organizing them by year and month. No emails will be deleted from Gmail.

---

#### **Example 2: Deleting Emails from a Specific Label**
You left GmailArchiver Corp, and all their communication is labeled as `GmailArchiver`. Archive and delete these emails.

```bash
python gmail_archiver.py --label GmailArchiver --delete --base-path ./gmail_archives
```

**What it does?**  
This archives all emails tagged with the `GmailArchiver` label, stores them in the specified path, and deletes them from Gmail after archiving.

---

#### **Example 3: Archiving Emails from a Specific Date Range**
You want to archive emails from January 1, 2022, to December 31, 2022, without deleting them.

```bash
python gmail_archiver.py --start-date 01-01-2022 --end-date 12-31-2022 --base-path ./gmail_archives_2022
```

**What it does?**  
This command archives all emails within the specified date range and saves them in the `./gmail_archives_2022` directory. Emails are retained in Gmail.

---

#### **Example 4: Archiving Emails Based on a Query**
You want to archive emails containing the word "invoice" without deleting them.

```bash
python gmail_archiver.py --query "invoice" --base-path ./invoice_archives
```

**What it does?**  
The tool searches for emails with "invoice" in their content or metadata and archives them in the specified directory. Emails remain in Gmail.

---

#### **Example 5: Archiving with Both Label and Query Filters**
You want to archive emails labeled `Work` that mention the word "meeting."

```bash
python gmail_archiver.py --label Work --query "meeting" --base-path ./work_meeting_archives
```

**What it does?**  
This archives all emails labeled `Work` that contain "meeting" in their content or metadata. Emails are saved in the specified directory.

---

#### **Example 6: Archiving and Deleting Old Emails**
You want to archive and delete all emails received before January 1, 2021.

```bash
python gmail_archiver.py --end-date 12-31-2020 --delete --base-path ./old_emails
```

**What it does?**  
This archives emails up to December 31, 2020, stores them in the specified directory, and deletes them from Gmail.

---

#### **Example 7: Archiving Emails from a Specific Start Date**
You want to archive emails from January 1, 2023, onwards without deleting them.

```bash
python gmail_archiver.py --start-date 01-01-2023 --base-path ./recent_emails
```

**What it does?**  
This archives emails from January 1, 2023, to the present, saving them in the specified directory.

---

#### **Example 8: Archiving Important Starred Emails**
You want to archive all emails marked as `Starred` in Gmail without deleting them.

```bash
python gmail_archiver.py --label STARRED --base-path ./starred_archives
```

**What it does?**  
This archives all starred emails into the specified directory, keeping them in Gmail.

---

#### **Example 9: Archiving Emails for Backup Before Leaving a Job**
Before leaving a job, you want to archive emails tagged as `Work` for safekeeping.

```bash
python gmail_archiver.py --label Work --base-path ./job_backup --delete
```

**What it does?**  
This archives emails labeled `Work`, stores them in the specified directory, and deletes them from Gmail.

---

#### **Example 10: Archiving Emails with Large Attachments**
You want to archive emails with attachments over 10 MB in size.

```bash
python gmail_archiver.py --query "size:10485760" --base-path ./large_attachments
```

**What it does?**  
This searches for emails with attachments larger than 10 MB, archives them, and retains them in Gmail.

---

#### **Example 11: Combining Start Date, Label, and Query**
You want to archive all `Work` emails starting from January 1, 2022, containing the word "project."

```bash
python gmail_archiver.py --start-date 01-01-2022 --label Work --query "project" --base-path ./project_emails
```

**What it does?**  
This archives all emails labeled `Work`, received after January 1, 2022, and containing the word "project."

---

#### **Example 12: Archiving Emails with No Query or Label**
You want to archive all emails in your Gmail account without using specific filters.

```bash
python gmail_archiver.py --base-path ./all_emails
```

**What it does?**  
This archives all emails, regardless of labels or queries, into the specified directory. Emails remain in Gmail.

---

With these examples, you can see the versatility of the Gmail Archiver tool to manage and organize your Gmail data effectively! 📨


Here are several sample commands with explanations for running `gmail_archiver.py` with different configurations:

1. **Basic Archiving with Default Settings**

   ```bash
   $ python gmail_archiver.py
   ```

   This command will prompt you interactively to:
   - Specify a base path for saving email archives (default: `./gmail_archives`).
   - Enter a cutoff date for archiving (e.g., `MM-DD-YYYY`).
   - Choose whether to delete emails from Gmail after archiving (type `yes` or `no`).

   The script will download and archive emails, saving them in the specified base path and optionally deleting them from Gmail.

---

2. **Archiving Emails in a Specific Date Range**

   ```bash
   $ python gmail_archiver.py --start-date 12-31-2004 --end-date 12-31-2005 --base-path "gmail_backup"
   ```

   - `--start-date`: Sets the start date for emails to be archived (`12-31-2004`).
   - `--end-date`: Sets the end date for emails to be archived (`12-31-2005`).
   - `--base-path`: Specifies the directory to store the archived emails (`gmail_backup`).

   This command archives emails from December 31, 2004, to December 31, 2005, and saves them in the `gmail_backup` directory. 

---

3. **Archiving with Deletion Enabled**

   ```bash
   $ python gmail_archiver.py --start-date 01-01-2020 --end-date 12-31-2020 --base-path "2020_archive" --delete
   ```

   - `--start-date`: Archives emails starting from January 1, 2020.
   - `--end-date`: Archives emails up to December 31, 2020.
   - `--base-path`: Sets the archive folder to `2020_archive`.
   - `--delete`: Deletes archived emails from Gmail after successful download.

   This command archives all emails from the year 2020 and removes them from Gmail once archived.

---

4. **Specifying a Custom Number of Threads**

   ```bash
   $ python gmail_archiver.py --start-date 01-01-2019 --end-date 12-31-2019 --threads 20
   ```

   - `--threads`: Sets the number of threads for processing emails concurrently (`20`).

   This command archives emails for the year 2019 with a custom setting of `20` threads for concurrent processing, which may speed up the archiving process on systems with sufficient resources.

---

5. **Setting a High Retry Count for Rate-Limiting Issues**

   ```bash
   $ python gmail_archiver.py --start-date 01-01-2018 --end-date 12-31-2018 --retries 10
   ```

   - `--retries`: Specifies the maximum number of retries if rate limits are encountered (`10`).

   This command archives emails for the year 2018 and allows up to `10` retries per email if rate limits are hit, making it more resilient in case of throttling.

---

6. **Combining Multiple Options**

   ```bash
   $ python gmail_archiver.py --start-date 01-01-2015 --end-date 12-31-2016 --base-path "2015_2016_backup" --delete --threads 15 --retries 7
   ```

   - Combines `--start-date`, `--end-date`, `--base-path`, `--delete`, `--threads`, and `--retries`.

   This command:
   - Archives emails from January 1, 2015, to December 31, 2016.
   - Saves them to `2015_2016_backup`.
   - Deletes emails from Gmail after archiving.
   - Uses `15` threads for concurrent processing.
   - Sets `7` retries in case of rate-limiting.

   This configuration is suitable for handling a large volume of emails efficiently with resiliency against rate-limiting.

---

## Configuration Parameters

You can adjust parameters directly in `gmail_archiver.py`:

- **MAX_WORKERS**: Sets the maximum number of concurrent threads for faster downloads.
- **Log File**: The `processed.log` file in the archive directory keeps track of archived months, allowing for resumable runs.

---

## Notes

- **Token Storage**: This tool uses a `token.json` file to store Google OAuth tokens, allowing it to access Gmail without re-authentication.
- **Compression Size Limit**: Monthly archives smaller than 500 KB are deleted automatically to save space.
- **Logging**: Processed months are logged to avoid redundant downloads on subsequent runs.

---

## Troubleshooting

- **Authentication Errors**: Ensure `credentials.json` exists in the same directory. Delete `token.json` if re-authentication is required.
- **Rate Limits**: If the tool hits Gmail API rate limits, it will retry automatically but may require manual intervention if persistent.

---
