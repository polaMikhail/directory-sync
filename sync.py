import argparse
import logging
import shutil
import os
import pycron
from cron_validator import CronValidator


def get_files(dir_path):
    """
    Returns a dictionary containing file paths and their respective last modified times, 
    as well as a set of unique file names in the given directory and its subdirectories.
    
    Parameters:
    dir_path (str): A string representing the directory path to search for files.
    
    Returns:
    A tuple containing two elements:
        - A dictionary containing file paths and their respective last modified times.
        - A set of unique file names in the given directory and its subdirectories.
    """
    file_dict = {}
    file_names_set = set()
    
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            # Add file path with last modified time to dictionary
            file_path = os.path.join(root, filename)
            file_dict[file_path] = os.path.getmtime(file_path)
            
            # Add file name to set
            file_name = file_path[len(dir_path):]
            file_names_set.add(file_name)
    
    return file_dict, file_names_set


def sync_common_files(args, src_dir_files, dest_dir_files, src_dir_map, dest_dir_map):
    """
    Synchronizes files that are present in both the source and destination directories,
    but have different modification times.

    Parameters:
        args (argparse.Namespace): An object containing command line arguments.
        src_dir_files (set): A set of files present in the source directory.
        dest_dir_files (set): A set of files present in the destination directory.
        src_dir_map (dict): A dictionary containing the modification times of files in the source directory.
        dest_dir_map (dict): A dictionary containing the modification times of files in the destination directory.

    Returns:
        None
    """
    # Find the files that are present in both the source and destination directories
    common_files = src_dir_files & dest_dir_files

    # Copy each file from the source directory to the destination directory if it has been modified more recently
    for file in common_files:
        src_path = os.path.join(args.src_dir, file)
        dest_path = os.path.join(args.dest_dir, file)
        if dest_dir_map[dest_path] < src_dir_map[src_path]:
            shutil.copy(src_path, dest_path)
            logging.info(f"Copied {src_path} to {dest_path}")
            print(f"Synced {file}")  # Optionally print a message for each synced file


def delete_files_from_dest_dir(args, src_dir_files, dest_dir_files):
    """
    Deletes files that are only present in the destination directory.

    Parameters:
        args (argparse.Namespace): An object containing command line arguments.
        src_dir_files (set): A set of files present in the source directory.
        dest_dir_files (set): A set of files present in the destination directory.

    Returns:
        None
    """
    # Determine which files exist only in the destination directory
    files_only_in_dest_dir = dest_dir_files - src_dir_files

    # Delete each file that exists only in the destination directory
    for dest_file in files_only_in_dest_dir:
        dest_path = os.path.join(args.dest_dir, dest_file)
        if os.path.isfile(dest_path):
            os.remove(dest_path)
            logging.info(f"Deleted {dest_path}")

        # Remove empty directories that contained the deleted file
        dest_dir = os.path.dirname(dest_path)
        while dest_dir != args.dest_dir:
            try:
                os.rmdir(dest_dir)
                logging.info(f"Removed empty directory {dest_dir}")
            except OSError:
                # Stop trying to remove directories if they still contain files
                break
            dest_dir = os.path.dirname(dest_dir)

def copy_files_from_src_to_dest(args, src_dir_files, dest_dir_files):
    """
    Copies files that are only present in the source directory to the destination directory.

    Parameters:
        args (argparse.Namespace): An object containing command line arguments.
        src_dir_files (set): A set of files present in the source directory.
        dest_dir_files (set): A set of files present in the destination directory.
    """
    # Determine which files exist only in the source directory
    files_only_in_src_dir = src_dir_files - dest_dir_files

    # Copy each file that exists only in the source directory to the destination directory
    for src_file in files_only_in_src_dir:
        dest_path = os.path.join(args.dest_dir, src_file)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(os.path.join(args.src_dir, src_file), dest_path)
        logging.info(f"Created {dest_path}")

def sync(args):
    """
    Synchronizes files between two directories.

    Parameters:
        args (argparse.Namespace): An object containing command line arguments.
    """
    src_dir = f"{args.src_dir}/" if args.src_dir[-1] != "/" else args.src_dir
    dest_dir = f"{args.dest_dir}/" if args.dest_dir[-1] != "/" else args.dest_dir
    src_dir_map, src_dir_files= get_files(src_dir)
    dest_dir_map, dest_dir_files = get_files(dest_dir)
    # if LAST_RUN_TIMESTAMP is set that means all the modified files should be copied
    copy_files_from_src_to_dest(args, src_dir_files, dest_dir_files)
    delete_files_from_dest_dir(args, src_dir_files, dest_dir_files)
    sync_common_files(args, src_dir_files, dest_dir_files, src_dir_map, dest_dir_map)


def setup_logger(filename):
    """
    Sets up a logger for the 'Folder Sync' module, with logs saved to a file and printed to the console.

    Parameters:
        filename (str): The name of the file to save the logs to.
    """
    logging.basicConfig(
        filename=filename,
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    )

    logger = logging.getLogger("Folder Sync")
    logger.setLevel(logging.INFO)

    # Also log to console.
    console = logging.StreamHandler()
    logger.addHandler(console)


def parse_args():
    """
    Parses command-line arguments and returns an object containing the options.

    Returns:
        argparse.Namespace: An object containing command-line options.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--src_dir", type=str, help="src directory to be monitored"
    )
    parser.add_argument(
        "-d", "--dest_dir", type=str, help="dest directory to be synced"
    )
    parser.add_argument(
        "-i", "--interval", type=str, help="cron time to sync files e.g. */5 * * * *"
    )
    parser.add_argument(
        "-l",
        "--log_file",
        type=str,
        help="path to log file e.g. /var/log/folder_sync.log",
    )
    parsed_args = parser.parse_args()

    # Validate arguments
    if not parsed_args.src_dir:
        parser.error("Source directory not specified.")
    if not parsed_args.dest_dir:
        parser.error("Destination directory not specified.")
    if not os.path.isdir(parsed_args.src_dir):
        parser.error("Source directory not found.")
    if not os.path.isdir(parsed_args.dest_dir):
        parser.error("Destination directory not found.")
    if not parsed_args.interval:
        parser.error("Interval not specified.")
    # Validate log file path if specified
    if parsed_args.log_file and not os.path.isfile(parsed_args.log_file):
        parser.error("Log file not found.")
    # Validate cron syntax for interval
    if not CronValidator().parse(parsed_args.interval):
        parser.error("Invalid cron syntax for interval.")

    return parsed_args


if __name__ == "__main__":
    args = parse_args()
    setup_logger(args.log_file)

    while True:
        if pycron.is_now(args.interval):
            sync(args)
