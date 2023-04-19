# Directory Sync

Directory Sync is a Python script for synchronizing files between two directories. It is designed to be run on a regular basis (e.g., via cron) to ensure that the two directories are kept in sync.

## How it Works
The script works by first getting a list of all files in both the source and destination directories, along with their last modified times. It then compares the two lists to determine which files need to be synced.

If a file exists in both directories but has a more recent modification time in the source directory, the script copies the file from the source directory to the destination directory.

If a file exists only in the destination directory, the script deletes the file.

If a file exists in both directories but has the same modification time, the script does nothing.

Finally, if a file exists only in the source directory, the script copies the file to the destination directory.

## Local usage
1. install the requirements using pip e.g  
`pip install -r requirements.txt`

2. Run the script e.g .
`python sync.py -s /path/to/source -d /path/to/destination -i "*/5 * * * *" -l /path/to/log/file.log`

3. To stop the script, press Ctrl+C on your keyboard

It's recommended to create python virtual environment 
https://docs.python.org/3/library/venv.html

## Requirements
1. Python 3.7 or higher
2. The pycron and cron_validator Python modules (can be installed using pip)