import os
import subprocess
import shutil
import smtplib
from email.mime.text import MIMEText

# Define directories with correct escape sequences
source_dir = r'C:\SQLBackupProduction'
loaded_dir = r'C:\SQLBackupProduction\Loaded'

# Email configuration
smtp_server = 'smtp.thmahc.com'  # Replace with your SMTP server
smtp_port = 25  # Replace with the SMTP port
sender_email = 'pcc_tasks@thmahc.com'
receiver_email = 'ETL_Alerts@amhealthpartners.com'
subject = 'SQL Backup Restoration Failed'
body = 'The SQL Backup restoration process failed. Please check the system for more details.'

# Function to send an email alert
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

try:
    # Check if the source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory does not exist: {source_dir}")
        exit(1)

    # Find the .SQB file in the source directory
    file_name = None
    for file in os.listdir(source_dir):
        if file.endswith('.SQB'):
            file_name = file
            break

    if file_name is None:
        print(f"No SQB files found in {source_dir}.")
        exit(1)

    # Full paths
    source_file = os.path.join(source_dir, file_name)
    loaded_file = os.path.join(loaded_dir, file_name)

    # CMD command to run SQL Backup with 'sa' credentials
    cmd = (
        f'"C:\\Program Files (x86)\\Red Gate\\SQL Backup 10\\(LOCAL)\\SQLBackupC.exe" '
        f'-U sa -P Tnhe@lth '
        f'-SQL "RESTORE LOG [PCC] FROM DISK = \'{source_file}\' '
        f'WITH PASSWORD = \'0exLRKGsqg)6DaXJudScJpM3fSj44L3P\', '
        f'STANDBY = \'C:\\Program Files\\Microsoft SQL Server\\MSSQL16.MSSQLSERVER\\MSSQL\\Backup\\Undo_PCC.dat\', '
        f'ORPHAN_CHECK"'
    )

    # Execute the CMD command
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True)

    # Check if the command was successful
    if result.returncode != 0:
        print(f"SQL Backup command failed with exit code: {result.returncode}")
        send_email_alert(subject, body)
        exit(result.returncode)

    # Move the file to the Loaded directory on success
    shutil.move(source_file, loaded_file)
    print(f"File {file_name} moved to {loaded_file} and source deleted.")

except FileNotFoundError as e:
    print(f"Error: {e}")
    send_email_alert(subject, f"File not found error: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    send_email_alert(subject, f"An unexpected error occurred: {e}")
    exit(1)
