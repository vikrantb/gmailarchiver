
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
1. **Create a Google Cloud Project**
   - Go to the [Google Cloud Console Project Creation page](https://console.cloud.google.com/projectcreate).
   - If you already have a project, skip to **Step 3.3**. Otherwise, create a new project by entering a **Project Name** and selecting **No organization** (if applicable).
   - Click **Create** to finish creating your project.

2. **Enable the Gmail API for Your Project**
   - Once your project is created, navigate to the **Enable API and Services** page for the Gmail API by clicking [here](https://console.cloud.google.com/apis/enableflow?apiid=gmail.googleapis.com).
   - Ensure you have the correct project selected in the top navigation bar.
   - Click **Enable** to activate the Gmail API for your project.

3. **Create OAuth 2.0 Credentials**
   - Go to the [API Credentials page](https://console.cloud.google.com/apis/credentials) in Google Cloud Console to manage your API credentials.
   - Select your project from the drop-down menu if it’s not already selected.
   - If there are no existing credentials, you’ll need to create new ones:
     1. Click **Create Credentials** and select **OAuth client ID**.
     2. For **Application type**, choose **Desktop app**.
     3. Name your credentials (e.g., "Gmail Archiver Credentials") and click **Create**.
     4. A dialog will appear with the **OAuth Client ID**. Click **Download JSON** to save the `credentials.json` file.

4. **Save the Credentials File**
   - Download the `credentials.json` file to your local machine.
   - Move the downloaded file to the directory where the Gmail Archiver script is located (e.g., `gmail_archiver/`).
   - Rename the file to `credentials.json`.

5. **Verify Setup**
   - Open your terminal or command prompt and run the Gmail Archiver script.
   - During the first run, the script will prompt you to authenticate. Follow the on-screen instructions to complete the OAuth authentication.

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

### Example

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
