'''this is a daemon for backuping data'''

from datetime import datetime, timedelta
import logging
import os
import re
import time
import zipfile

DEFAULT_BACKUP_INTERVAL_S = 60 * 60 # 1 hour
BACKUP_FILE_PREFIX = 'cb_backup'
BACKUP_FILE_SUFFIX = '.zip'
# example: cb_backup-20201231-123301.zip
BACKUP_FILE_RE = re.compile(BACKUP_FILE_PREFIX + r'-(\d{8})-(\d{6})' + BACKUP_FILE_SUFFIX + r'$')

class Configuration():
    def __init__(self):
        self.mapper_path = os.getenv('MAPPER_PATH')
        self.temp_path = os.getenv('TEMP_PATH')
        self.db_path = os.getenv('CB_DB_PATH')
        self.backup_path = os.getenv('BACKUP_PATH')
        self.sqlite_tools_path = os.getenv('SQLITE_TOOLS_PATH')
        self.log_path = os.getenv('LOG_PATH')
        self.backup_interval_s = os.getenv('BACKUP_INTERVAL', DEFAULT_BACKUP_INTERVAL_S)
        
def validate_env(c: Configuration):
    # check if the environment is ready for backup
    # if not, raise an exception
    # validate the user mapper path
    if not os.path.exists(c.mapper_path) or not os.path.isfile(c.mapper_path):
        raise Exception(f"mapper file '{c.mapper_path}' does not exist")
    
    # validate the temp path
    if not os.path.exists(c.temp_path):
        os.makedirs(c.temp_path)
    elif not os.path.isdir(c.temp_path):
        raise Exception(f"temp path '{c.temp_path}' is not a directory")
    
    # validate the db path
    if not os.path.exists(c.db_path) or not os.path.isfile(c.db_path):
        raise Exception(f"db path '{c.db_path}' does not exist")

    # validate or create the backup path
    if not os.path.exists(c.backup_path):
        os.makedirs(c.backup_path)
    elif not os.path.isdir(c.backup_path):
        raise Exception(f"backup path '{c.backup_path}' is not a directory")
    
    # validate the sqlit3 command
    if os.system(f'{os.path.join(c.sqlite_tools_path, 'sqlite3')} --version') != 0:
        raise Exception("sqlite3 command not found")
    
    # validate the log path
    if not os.path.exists(c.log_path):
        os.makedirs(c.log_path)
    elif not os.path.isdir(c.log_path):
        raise Exception(f"log path '{c.log_path}' is not a directory")

def get_next_backup_time(c: Configuration):
    # get all the backup files
    print("backup path is ", c.backup_path) # XXX - debug
    backup_files = [fname for fname in os.listdir(c.backup_path) if BACKUP_FILE_RE.match(fname)]
    backup_files.sort()
    print("backup files are ", backup_files) # XXX - debug
    if len(backup_files) == 0:
        # no backup files found, return now
        return datetime.now() - timedelta(seconds=1)
    
    # parse the last backup file name
    m = BACKUP_FILE_RE.match(backup_files[-1])
    last_backup_time = datetime(int(m.group(1)[0:4]), int(m.group(1)[4:6]), int(m.group(1)[6:8]), 
                    int(m.group(2)[0:2]), int(m.group(2)[2:4]), int(m.group(2)[4:6]))
    
    return last_backup_time + timedelta(seconds=c.backup_interval_s)

def dump_db(c: Configuration) -> str:
    # dump the db to a temp file
    temp_file_name = os.path.join(c.temp_path, f"{BACKUP_FILE_PREFIX}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sql")
    res = os.system(f"{os.path.join(c.sqlite_tools_path, 'sqlite3')} {c.db_path} .dump > {temp_file_name}")
    if res != 0:
        raise Exception(f"Failed to dump the database to {temp_file_name}")

    return temp_file_name

def create_backup(c: Configuration):
    # backup the data
    temp_file_name = dump_db(c)
    backup_file_name = os.path.basename(temp_file_name).replace('.sql', BACKUP_FILE_SUFFIX)
        
    with zipfile.ZipFile(os.path.join(c.backup_path, backup_file_name), 'w') as backup_file:
        backup_file.write(c.mapper_path, os.path.basename(c.mapper_path))
        backup_file.write(temp_file_name, os.path.basename(temp_file_name))
        
    print(f"Backup file created at {os.path.join(c.backup_path, backup_file_name)}") # XXX - debug

def main():
    # make sure that environment is ready
    configuration = Configuration()
    validate_env(configuration)
    logging.basicConfig(filename=os.path.join(configuration.log_path, 'backupd.log'), level=logging.INFO)

    next_backup_time = get_next_backup_time(configuration)
    print(f"Next backup time is {next_backup_time}") # XXX - debug
    while True:
        now = datetime.now()
        if now > next_backup_time:
            print("Creating backup") # XXX - debug
            create_backup(configuration)
            next_backup_time += timedelta(seconds=configuration.backup_interval_s)

            # todo - delete old backup files
        
        time.sleep(60)

if __name__ == '__main__':
    main()