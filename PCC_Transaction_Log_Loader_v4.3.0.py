import os
import json
import subprocess
import shutil
import smtplib
from email.mime.text import MIMEText

# Load configuration from the JSON file
config_file_path = r'C:\Scripts\Python\Productiton\Configuration\PCC_SQL_BCK_Configuration.json'
with open(config_file_path, 'r') as config_file:
    CONFIG = json.load(config_file)

# Configuration
source_dir = CONFIG['backup_directory']
production_scripts = CONFIG['production_scripts']
loaded_dir = os.path.join(source_dir, 'Loaded')

# SQL Server and Database configuration
sql_server = CONFIG['sql_server']
sql_user = CONFIG['sql_user']
sql_password = CONFIG['sql_password']
sql_backup_password = CONFIG['sql_backup_password']
database_name = CONFIG['database_name']

# Email configuration
smtp_server = CONFIG['smtp_server']
smtp_port = CONFIG['smtp_port']
sender_email = CONFIG['sender_email']
receiver_email = CONFIG['receiver_email']
subject = 'SQL Backup Restoration Failed - Step 2 - Apply Transaction Log'
body = f'The SQL Backup restoration process failed on {sql_server} @ {production_scripts}. Please check the system log file for more details.'

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
        send_email_alert(subject, f"Source directory does not exist: {source_dir}")
        exit(1)

    # Find the .SQB file in the source directory
    file_name = None
    for file in os.listdir(source_dir):
        if file.endswith('.SQB'):
            file_name = file
            break

    if file_name is None:
        print(f"No SQB files found in {source_dir}.")
        send_email_alert(subject, f"No SQB files found in {source_dir}.")
        exit(1)

    # Full paths
    source_file = os.path.join(source_dir, file_name)
    loaded_file = os.path.join(loaded_dir, file_name)

    # Use sqlcmd to set the database to SINGLE_USER mode
    set_single_user_cmd = (
        f'sqlcmd -S {sql_server} -U {sql_user} -P {sql_password} -Q "ALTER DATABASE [{database_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;"'
    )

    # Execute the command to set database to SINGLE_USER
    try:
        print(f"Setting {database_name} database to SINGLE_USER mode.")
        result = subprocess.run(set_single_user_cmd, shell=True, capture_output=True, text=True, timeout=15)
        print(result.stdout)
        print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"Setting {database_name} to SINGLE_USER mode timed out.")
        send_email_alert(subject, f"Timeout: Setting {database_name} to SINGLE_USER mode took too long.")
        exit(1)

    if result.returncode != 0:
        print(f"Failed to set {database_name} database to SINGLE_USER mode with exit code: {result.returncode}")
        send_email_alert(subject, f"Failed to set {database_name} database to SINGLE_USER mode.")
        exit(result.returncode)

    # CMD command to run SQL Backup
    restore_cmd = (
        f'"C:\\Program Files (x86)\\Red Gate\\SQL Backup 10\\(LOCAL)\\SQLBackupC.exe" '
        f'-U {sql_user} -P {sql_password} '
        f'-SQL "RESTORE LOG [{database_name}] FROM DISK = \'{source_file}\' '
        f'WITH PASSWORD = \'{sql_backup_password}\', '
        f'STANDBY = \'C:\\Program Files\\Microsoft SQL Server\\MSSQL16.MSSQLSERVER\\MSSQL\\Backup\\Undo_{database_name}.dat\', '
        f'ORPHAN_CHECK"'
    )

    # Execute the CMD command for restoration
    try:
        print(f"Executing: SQL Backup command for {database_name}")
        result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=15)
        print(result.stdout)
        print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"SQL Backup command for {database_name} timed out.")
        send_email_alert(subject, f"Timeout: SQL Backup command for {database_name} took too long.")
        exit(1)

    # Check if the command was successful or returned the warning code 472 (orphaned users)
    if result.returncode == 0 or result.returncode == 472:
        # Move the file to the Loaded directory
        shutil.move(source_file, loaded_file)
        print(f"File {file_name} moved to {loaded_file} and source deleted.")

        # Use sqlcmd to set the database back to MULTI_USER mode
        set_multi_user_cmd = (
            f'sqlcmd -S {sql_server} -U {sql_user} -P {sql_password} -Q "ALTER DATABASE [{database_name}] SET MULTI_USER;"'
        )

        # Execute the command to set database back to MULTI_USER
        try:
            print(f"Setting {database_name} database back to MULTI_USER mode.")
            result = subprocess.run(set_multi_user_cmd, shell=True, capture_output=True, text=True, timeout=15)
            print(result.stdout)
            print(result.stderr)
        except subprocess.TimeoutExpired:
            print(f"Setting {database_name} back to MULTI_USER mode timed out.")
            send_email_alert(subject, f"Timeout: Setting {database_name} back to MULTI_USER mode took too long.")
            exit(1)

        if result.returncode != 0:
            print(f"Failed to set {database_name} database back to MULTI_USER mode with exit code: {result.returncode}")
            send_email_alert(subject, f"Failed to set {database_name} database back to MULTI_USER mode.")
            exit(result.returncode)

    else:
        print(f"SQL Backup command failed with exit code: {result.returncode}")
        send_email_alert(subject, body)
        exit(result.returncode)

except FileNotFoundError as e:
    print(f"Error: {e}")
    send_email_alert(subject, f"FileNotFoundError: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    send_email_alert(subject, f"Unexpected error: {e}")
    exit(1)
