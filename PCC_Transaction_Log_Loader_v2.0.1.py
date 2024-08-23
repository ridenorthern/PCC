import os
import subprocess
import shutil
import sys
import ctypes

# Function to check if the script is running as an administrator
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# If not running as admin, re-run the script with admin privileges
if not is_admin():
    print("Script is not running as administrator. Re-launching with elevated privileges...")
    # Re-run the script with elevated privileges
    params = ' '.join([f'"{x}"' for x in sys.argv])
    subprocess.run(['runas', '/user:Administrator', f'cmd /c python {params}'], shell=True)
    sys.exit()

# Define directories with correct escape sequences
source_dir = r'C:\SQLBackupProduction'
loaded_dir = r'C:\SQLBackupProduction\Loaded'

try:
    # Check if the source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory does not exist: {source_dir}")
        sys.exit(1)

    # Find the .SQB file in the source directory
    file_name = None
    for file in os.listdir(source_dir):
        if file.endswith('.SQB'):
            file_name = file
            break

    if file_name is None:
        print(f"No SQB files found in {source_dir}.")
        sys.exit(1)

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
        sys.exit(result.returncode)

    # Move the file to the Loaded directory
    shutil.move(source_file, loaded_file)
    print(f"File {file_name} moved to {loaded_file} and source deleted.")

except FileNotFoundError as e:
    print(f"Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)
