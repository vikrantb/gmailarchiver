import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

def sanitize_filename(filename, max_length=100):
    """
    Sanitizes a string to be used as a safe filename.
    """
    sanitized = ''.join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
    return sanitized[:max_length]

def write_emails_to_disk(email_buffer, folder_path):
    """
    Writes buffered emails to disk.
    """
    for email_data in email_buffer:
        email_folder_path = os.path.join(folder_path, email_data['folder_name'])
        os.makedirs(email_folder_path, exist_ok=True)

        # Save email content
        for content_type, content in email_data['content_parts']:
            filename = 'email.txt' if content_type == 'text/plain' else 'email.html'
            filepath = os.path.join(email_folder_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        # Save headers
        headers_filepath = os.path.join(email_folder_path, 'headers.txt')
        with open(headers_filepath, 'w', encoding='utf-8') as f:
            for header, value in email_data['headers'].items():
                f.write(f"{header}: {value}\n")

        # Save attachments
        for attachment in email_data['attachments']:
            file_path = os.path.join(email_folder_path, attachment['filename'])
            with open(file_path, 'wb') as f:
                f.write(attachment['data'])

def compress_folder(folder_path):
    """
    Compresses a folder into a zip file and removes the original folder.
    """
    shutil.make_archive(folder_path, 'zip', folder_path)
    shutil.rmtree(folder_path)