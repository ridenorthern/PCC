import os
import json
import paramiko
from stat import S_ISDIR
import smtplib
from email.mime.text import MIMEText

# Load configuration from the JSON file
config_file_path = r'C:\Scripts\Python\Productiton\Configuration\PCC_SQL_BCK_Configuration.json'
with open(config_file_path, 'r') as config_file:
    CONFIG = json.load(config_file)

# Configuration
sftp_host = CONFIG['sftp_host']
sftp_username = CONFIG['sftp_username']
sftp_password = CONFIG['sftp_password']
sftp_directory = CONFIG['sftp_directory']
backup_directory = CONFIG['backup_directory']
production_scripts = CONFIG['production_scripts']

# SQL Server and Database configuration
sql_server = CONFIG['sql_server']
sql_user = CONFIG['sql_user']
sql_password = CONFIG['sql_password']
sql_backup_password = CONFIG['sql_backup_password']
database_name = CONFIG['database_name']

smtp_server = CONFIG['smtp_server']
smtp_port = CONFIG['smtp_port']
sender_email = CONFIG['sender_email']
receiver_email = CONFIG['receiver_email']
subject = 'PCC SQL Backup Restoration Failed - Step 1 - Get Latest File'
body = f'The PCC SQL Backup SFTP Retrieve Latest File process failed @ {production_scripts}. Please check the system log file for more details.'

# Function to send an email aler
def send_email_alert(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Notification email sent to {receiver_email}.")
    except Exception as e:
        print(f"Failed to send email notification: {e}")

# Ensure the backup directory exists
if not os.path.exists(backup_directory):
    try:
        os.makedirs(backup_directory)
    except Exception as e:
        error_message = f"Failed to create/access the directory {backup_directory}: {e}"
        print(error_message)
        send_email_alert("Backup Directory Error", error_message)
        exit(1)

# Establish an SFTP connection
def sftp_connect():
    try:
        transport = paramiko.Transport((sftp_host, 22))
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp
    except Exception as e:
        error_message = f"Failed to connect to SFTP server: {e}"
        print(error_message)
        send_email_alert("SFTP Connection Error", error_message)
        exit(1)

# Get the most recently modified file in the SFTP directory
def get_latest_file_sftp(sftp, directory):
    latest_file = None
    latest_time = None
    try:
        for entry in sftp.listdir_attr(directory):
            if not S_ISDIR(entry.st_mode):
                if latest_time is None or entry.st_mtime > latest_time:
                    latest_file = entry.filename
                    latest_time = entry.st_mtime
    except Exception as e:
        error_message = f"Failed to list files in SFTP directory: {e}"
        print(error_message)
        send_email_alert("SFTP Directory Listing Error", error_message)
        exit(1)
    return latest_file

# Download the latest file from SFTP
def download_latest_file(sftp, sftp_directory, backup_directory):
    latest_file = get_latest_file_sftp(sftp, sftp_directory)

    if latest_file:
        sftp_file_path = os.path.join(sftp_directory, latest_file)
        backup_file_path = os.path.join(backup_directory, latest_file)

        try:
            sftp.get(sftp_file_path, backup_file_path)
            print(f"Downloaded and saved the latest file: {latest_file} to {backup_directory}")
        except Exception as e:
            error_message = f"Failed to download {latest_file}: {e}"
            print(error_message)
            send_email_alert("SFTP Download Error", error_message)
            exit(1)
    else:
        message = "No files found in the SFTP directory to download."
        print(message)
        send_email_alert("No Files to Download", message)
        exit(1)

def main():
    # Connect to the SFTP server
    sftp = sftp_connect()

    # Download the latest file from SFTP to the local backup directory
    download_latest_file(sftp, sftp_directory, backup_directory)

    # Close the SFTP connection
    sftp.close()

if __name__ == "__main__":
    main()

