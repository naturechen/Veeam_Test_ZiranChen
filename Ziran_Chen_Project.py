import os
import shutil
import hashlib
import time
import logging
import argparse
from types import SimpleNamespace
import sys
from datetime import datetime

# Run python C:\Users\ChenZ\Desktop\TestProject\Ziran_Chen_Project.py "C:/Users/ChenZ/Desktop/TestProject/My_Source" "C:/Users/ChenZ/Desktop/TestProject/Duplicate" 10 "C:/Users/ChenZ/Desktop/TestProject/sync.log"

# Calculate the MD5 hash value of a file
def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f: # rb Read-only (binary mode), 'with open' will release and close the resource, when we finish calculation.
        for chunk in iter(lambda: f.read(1048576), b""):  # Read files in chunk to avoid memory overflow for large files, 1mb
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Synchronize two folders
def sync_folders(source_folder, replica_folder, logger):
    # Get all files/folders in source and copy folders
    source_items = set(os.listdir(source_folder))
    replica_items = set(os.listdir(replica_folder))

    # 1. Process the existing content in the source folder (create/update a copy)
    for item in source_items:
        source_path = os.path.join(source_folder, item) # combine path and file, Automatically select the appropriate path separator
        replica_path = os.path.join(replica_folder, item)

        if os.path.isdir(source_path):
            # If it is a directory, recursively synchronize
            if not os.path.exists(replica_path):
                os.makedirs(replica_path) # create directory into backup file
                logger.info(f"Create a Directory：{replica_path}")

            sync_folders(source_path, replica_path, logger)
        else:
            # If it is a file, check whether it needs to be updated
            if not os.path.exists(replica_path):
                # The file does not exist in the replica, copy it directly
                shutil.copy2(source_path, replica_path)
                logger.info(f"Copy the new file：{replica_path}")
            else:
                # Compare two folders and decide whether to update
                src_stat = os.stat(source_path)
                rep_stat = os.stat(replica_path)
        
                 # size differences
                if src_stat.st_size != rep_stat.st_size:
                    shutil.copy2(source_path, replica_path)
                    logger.info(f"Copy the new file：{replica_path}")
                    return True

                # Strict consistency check
                if calculate_md5(source_path) != calculate_md5(replica_path):
                    shutil.copy2(source_path, replica_path)
                    logger.info(f"Copy the new file：{replica_path}")
                    return True

    # 2. Process redundant content in the replica folder (delete content that does not exist in the source), 
    for item in replica_items - source_items: # Get the elements that exist in replica_items but not in source_items
        replica_path = os.path.join(replica_folder, item)
        if os.path.isdir(replica_path):
            shutil.rmtree(replica_path)
            logger.info(f"Deleting a Directory：{replica_path}")
        else:
            os.remove(replica_path)
            logger.info(f"Deleting files：{replica_path}")

# main funciton
def main():
    # Parsing command line arguments
    # python C:\Users\ChenZ\Desktop\TestProject\Ziran_Chen_Project.py "C:/Users/ChenZ/Desktop/TestProject/My_Source" "C:/Users/ChenZ/Desktop/TestProject/Duplicate" 10 "C:/Users/ChenZ/Desktop/TestProject/sync.log"
    parser = argparse.ArgumentParser(description="Folder synchronization tool (one-way synchronization)")
    parser.add_argument("source", type=str, help="Source folder path")
    parser.add_argument("replica", type=str, help="Copy folder path")
    parser.add_argument("interval", type=int, help="Sync Interval (seconds）")
    parser.add_argument("log_file", type=str, help="Log file path")
    args = parser.parse_args()

    # # test
    # args = SimpleNamespace(log_file = "C:/Users/ChenZ/Desktop/TestProject/sync.log", 
    #                        source = "C:/Users/ChenZ/Desktop/TestProject/My_Source",
    #                        replica = "C:/Users/ChenZ/Desktop/TestProject/Duplicate",
    #                        interval = 8
    #                        )

    # Configure logging (both to the console and to a file)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(args.log_file),
            logging.StreamHandler()  # Output to console
        ]
    )

    # Loop execution synchronization
    while True:
        logger = logging.getLogger()
        logger.info("Start Sync...")
        start_time = datetime.now()

        try:
            if args.interval <= 0:
                print("Interval time must be a positive integer.")
                sys.exit()

            # Check if the user create the duplicated folder or not
            if not os.path.exists(args.replica):
                os.makedirs(args.replica)
                logger.info(f"Create duplicate folder {args.replica}")
            
            # Check if the user create the Orginal Source folder or not
            if not os.path.exists(args.source):
                os.makedirs(args.source)
                logger.info(f"Create source folder {args.source}")

            sync_folders(args.source, args.replica, logger)
            logger.info("Sync Successful！")
            end_time = datetime.now()
            print(f"Spending time: {end_time-start_time}")

        except Exception as e:
            logger.error(f"Synchronization failed：{str(e)}")
        
        time.sleep(args.interval)  # Wait for the specified interval before syncing again

if __name__ == "__main__":
    main()