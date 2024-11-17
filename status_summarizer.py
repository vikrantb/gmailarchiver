def summarize_statistics(start_date, end_date, base_path, query, label, delete, total_emails, emails_downloaded, emails_deleted, attachments_saved, original_size,
                         space_saved, zip_files_created):
    """
    Summarizes and prints statistics about the Gmail archiving process.

    Args:
        start_date (str): The start date of the email retrieval in mm-dd-yyyy format.
        end_date (str): The end date of the email retrieval in mm-dd-yyyy format.
        base_path (str): Base path where emails are archived.
        query (str): Custom Gmail search query.
        label (str): Gmail label to filter emails.
        delete (bool): Whether emails were deleted after archiving.
        total_emails (int): Total number of emails retrieved from Gmail.
        emails_downloaded (int): Number of emails successfully downloaded.
        emails_deleted (int): Number of emails deleted (if deletion was enabled).
        attachments_saved (int): Total number of attachments saved.
        original_size (float): Original total size of the emails in bytes before compression.
        space_saved (float): Total disk space saved in bytes due to compression.
        zip_files_created (int): Number of zip files created during compression.
    """
    def format_size(size_in_bytes):
        """Converts bytes to a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} PB"

    # Prepare formatted sizes
    original_size_formatted = format_size(original_size)
    space_saved_formatted = format_size(space_saved)

    # Build the filter description
    filters = []
    if start_date and end_date:
        filters.append(f"from **{start_date}** to **{end_date}**")
    elif start_date:
        filters.append(f"starting from **{start_date}**")
    elif end_date:
        filters.append(f"up to **{end_date}**")
    if label:
        filters.append(f"label: **'{label}'**")
    if query:
        filters.append(f"query: **'{query}'**")
    filter_summary = ", ".join(filters) if filters else "**all emails**"

    # Determine the action type
    if delete:
        action_type = (
            f"📤 **Archived and deleted** **{emails_deleted}** emails, saving 💾 **{space_saved_formatted}** of disk space."
        )
    else:
        action_type = (
            f"📤 **Archived** **{emails_downloaded}** emails with 📎 **{attachments_saved} attachments**. "
            f"⚠️ While emails were not deleted, this could have saved 💾 **{space_saved_formatted}**."
        )

    # Build the compression summary
    compression_summary = f"📦 **Compression Complete**: Created **{zip_files_created}** zip files, shrinking emails from **{original_size_formatted}**."

    # Construct the final message
    final_message = (
        f"\n✨ **Gmail Archiving Summary** ✨\n\n"
        f"🔍 **Filters Applied**: {filter_summary}\n"
        f"📧 **Emails Processed**: **{total_emails}**\n"
        f"{action_type}\n"
        f"📂 **Data Stored At**: {base_path}\n"
        f"{compression_summary}\n\n"
        f"🔒 Your emails are now securely archived, beautifully organized, and ready for future use! 🚀\n"
    )

    # Add ASCII art representing a secure archive
    ascii_art = """
          ________________________
         |########################|
         |#  ________________   #|
         |# |                |  #|
         |# | Archiving Safe |  #|
         |# |________________|  #|
         |########################|
         |########################|
         |########################|
         |########################|
         |########################|
         \\########################/
          \\______________________/
    📨 Mission accomplished! Your data is securely saved and organized! 📂
    """

    # Combine message and ASCII art
    print(final_message)
    print(ascii_art)
