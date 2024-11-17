import email
import os
import shutil

space_saved, zip_files_created, original_size, attachments_saved = 0, 0, 0, 0
def write_buffer_to_disk(email_buffer, folder_path):
    """
    Writes buffered emails to disk organized by year/month.

    Args:
        email_buffer (list): A list of email data dictionaries.
        folder_path (str): The base folder path where emails will be saved.

    Returns:
        None
    """
    global attachments_saved
    for email_data in email_buffer:
        try:
            # Extract year and month from email's date
            date_str = email_data.get('date_str', '')
            parsed_date = email.utils.parsedate_to_datetime(date_str)
            year = parsed_date.strftime('%Y')
            month = parsed_date.strftime('%m')

            # Construct the year/month folder path
            year_month_path = os.path.join(folder_path, year, month)
            os.makedirs(year_month_path, exist_ok=True)  # Create year/month folder if it doesn't exist

            # Create the email-specific folder
            email_folder_path = os.path.join(year_month_path, email_data['folder_name'])
            os.makedirs(email_folder_path, exist_ok=True)

            # Save email content
            for content_type, content in email_data['content_parts']:
                if content_type == 'text/plain':
                    filename = 'email.txt'
                elif content_type == 'text/html':
                    filename = 'email.html'
                else:
                    continue
                filepath = os.path.join(email_folder_path, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Save headers
            headers_filepath = os.path.join(email_folder_path, 'headers.txt')
            with open(headers_filepath, 'w', encoding='utf-8') as f:
                f.write(f"From: {email_data['sender']}\n")
                f.write(f"Date: {email_data['date_str']}\n")
                f.write(f"Subject: {email_data['subject']}\n")
                for header, value in email_data['headers'].items():
                    f.write(f"{header}: {value}\n")

            # Save attachments
            for attachment in email_data['attachments']:
                attachments_saved += 1
                file_path = os.path.join(email_folder_path, attachment['filename'])
                with open(file_path, 'wb') as f:
                    f.write(attachment['data'])

        except Exception as e:
            print(f"Error writing email data to disk for {email_data['folder_name']}: {e}")


def compress_month_folder(folder_path):
    """
    Compresses each month-level folder.

    Args:
        folder_path (str): The base folder path where emails are saved.

    Returns:
        None
    """
    global space_saved, zip_files_created, original_size  # Declare as global to modify these variables

    for root, dirs, _ in os.walk(folder_path):
        for dir_name in dirs:
            month_folder = os.path.join(root, dir_name)
            if not os.path.isdir(month_folder):
                continue
            folder_size_before = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(month_folder)
                for filename in filenames
            )
            shutil.make_archive(month_folder, 'zip', month_folder)
            zip_files_created += 1  # Increment the global counter
            shutil.rmtree(month_folder)
            zip_size = os.path.getsize(f"{month_folder}.zip")
            original_size += folder_size_before  # Increment the global counter
            space_saved += folder_size_before - zip_size  # Increment the global space saved
            return space_saved, zip_files_created, original_size