import datetime
from enum import Enum
import functools
import inspect
import sqlite3
import uuid
from apscheduler.schedulers.background import BackgroundScheduler

from cb_server.jobs_lock import JobsLock

REQUIRED_DB_VERSION = 2

BALANCE_TABLE = 'user_balance'
USER_TABLE = 'user'
TRANACTIONS_TABLE = 'transactions'
VERSION_TABLE = 'version'
JOBS_TABLE = 'jobs'

USERID_KEY = 'userid'
BALANCE_KEY = 'balance'
OVERDRAFT_LIMIT_KEY = 'overdraft_limit'
VALUE_KEY = 'value'
TIMESTAMP_KEY = 'timestamp'
DESCRIPTION_KEY = 'description'
ID_KEY = 'id'
VERSION_KEY = 'version'
CRON_KEY = 'cron'
ACTION_KEY = 'action'
ACTION_PARAMS_KEY = 'action_params' # this is a json string
LAST_RUN_KEY = 'last_run'
LAST_RUN_STATUS_KEY = 'last_run_status'
LAST_RUN_ERROR_KEY = 'last_run_error'

class RepoException(Exception):
    pass

class UserNotFound(RepoException):
    pass

class ActionType(Enum):
    TRANSFER = 1

# this wrapper function is used to reuse the same connection for multiple calls
def reuse_conn(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if 'conn' is in kwargs
        params = inspect.signature(func).parameters
        if 'conn' not in params:
            raise ValueError(f"Function {func.__name__} does not have a 'conn' parameter")
        
        if kwargs.get('conn') is not None:
            return func(self, *args, **kwargs)
        
        conn = sqlite3.connect(self.db_path)
        kwargs['conn'] = conn
        try:
            result = func(self, *args, **kwargs)
            conn.commit()
            return result
        finally:
            conn.close()
    return wrapper

class Repo:
    @reuse_conn
    def get_database_version(self, conn: sqlite3.Connection=None) -> int:
        # check if the version table exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{VERSION_TABLE}'")    
        res = cursor.fetchone()
        cursor.close()
        if res is None:
            # no version table, this is a new database (version 0)
            return 0
        
        # get the version
        cursor = conn.cursor()
        cursor.execute(f'SELECT {VERSION_KEY} FROM {VERSION_TABLE}')
        res = cursor.fetchmany(2)
        if len(res) != 1:
            raise Exception(f"Database version table '{VERSION_TABLE}' exists but has {len(res)} rows")

        version = res[0][0]
        return version
    
    @reuse_conn
    def create_version_table(self, conn: sqlite3.Connection=None, version:int=REQUIRED_DB_VERSION):
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE {VERSION_TABLE} (
                {VERSION_KEY} INTEGER NOT NULL
            )
        ''')
        cursor.execute(f'INSERT INTO {VERSION_TABLE} ({VERSION_KEY}) VALUES ({version})')
        cursor.close()

    def set_db_version(self, version: int, conn: sqlite3.Connection):
        if self.get_database_version(conn=conn) == 0:
            self.create_version_table(conn=conn, version=version)
        else:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE {VERSION_TABLE} SET {VERSION_KEY}=?', (version,))
            cursor.close()

    @reuse_conn
    def create_jobs_table(self, conn: sqlite3.Connection=None):
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {JOBS_TABLE} (
                {USERID_KEY} TEXT PRIMARY KEY,
                {CRON_KEY} TEXT NOT NULL,
                {ACTION_KEY} INTEGER NOT NULL,
                {ACTION_PARAMS_KEY} TEXT NOT NULL, 
                {DESCRIPTION_KEY} TEXT NOT NULL, 
                {LAST_RUN_KEY} INTEGER NOT NULL, 
                {LAST_RUN_STATUS_KEY} INTEGER NOT NULL,
                {LAST_RUN_ERROR_KEY} TEXT NOT NULL,
            )
        ''')

    def backward_compatibility(self):
        # get database version
        is_migrated = False
        with sqlite3.connect(self.db_path) as conn:
            db_version = self.get_database_version(conn=conn)
            while db_version < REQUIRED_DB_VERSION:
                is_migrated = True
                print(f"upgrading database from version {db_version} to {db_version + 1}")
                if db_version == 0:
                    # no need to explicitly create the version table, it will be done by 'set_db_version'
                    pass
                elif db_version == 1:
                    # create the 'jobs' table
                    self.create_jobs_table(conn=conn)
                else:
                    raise Exception(f"Unknown database version {db_version}")

                self.set_db_version(db_version + 1, conn=conn)
                
                # we commit after each version upgrade
                conn.commit()   
                db_version = self.get_database_version(conn=conn)

        if is_migrated:
            print("Database migration completed.", end=" ")
    
        print(f"Database is up to date (version={db_version})")

    def create_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Create the 'balance' table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {BALANCE_TABLE} (
                {USERID_KEY} TEXT PRIMARY KEY,
                {BALANCE_KEY} REAL NOT NULL
            )
        ''')
        # Create the 'user' table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {USER_TABLE} (
                {USERID_KEY} TEXT PRIMARY KEY,
                {OVERDRAFT_LIMIT_KEY} REAL NOT NULL
            )
        ''')
        # create the tranctions table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TRANACTIONS_TABLE} (
                {USERID_KEY} TEXT NOT NULL,
                {VALUE_KEY} REAL NOT NULL,
                {TIMESTAMP_KEY} INTEGER NOT NULL,
                {DESCRIPTION_KEY} TEXT NOT NULL,
                {ID_KEY} TEXT NOT NULL
            )
        ''')
        # create the version table
        self.create_version_table(conn)
        self.create_jobs_table(conn)
        conn.commit()
        conn.close()

    def process_jobs(self):
        pass

    def __init__(self, db_path: str, create: bool=False, ):
        thread_safe = sqlite3.threadsafety
        if thread_safe < 1:
            raise Exception(f"sqlite3 is not thread safe (level={thread_safe}). Level 1 or higher is required")
        
        self.db_path = db_path
        if create:
            self.create_database()
        else:
            self.backward_compatibility()

        # take the jobs lock so only one instance of the job processor is running at a time
        self.jobs_lock = JobsLock(db_path)
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.process_jobs, 'interval', seconds=10)
        scheduler.start()
        
    def get_user_balance(self, userid):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'SELECT {BALANCE_KEY} FROM {BALANCE_TABLE} WHERE {USERID_KEY}=?', (userid,))
        res = cursor.fetchone()
        if res is None:
            raise UserNotFound(f"User '{userid}' not found")
        
        return res[0]
    
    def add_user(self, userid, balance):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'INSERT INTO {USER_TABLE} ({USERID_KEY}, {OVERDRAFT_LIMIT_KEY}, {OVERDRAFT_LIMIT_KEY}) VALUES (?, ?, ?)', 
                       (userid, 0, 0))
        cursor.execute(f'INSERT INTO {BALANCE_TABLE} ({USERID_KEY}, {BALANCE_KEY}) VALUES (?, ?)', (userid, balance))
        conn.commit()
        conn.close()

        return True, None
    
    def force_add_transaction(self, userid: str, value: float, timestamp: int, description: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'''INSERT INTO {TRANACTIONS_TABLE} ({USERID_KEY}, {VALUE_KEY}, {TIMESTAMP_KEY}, {DESCRIPTION_KEY}, {ID_KEY}) 
            VALUES (?, ?, ?, ?, ?)''', (userid, value, timestamp, description, str(uuid.uuid4()))) 
        conn.commit()
        conn.close()

        return True, None
    
    def transfer_money(self, from_userid: str, to_userid: str, value: float, description: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'SELECT {BALANCE_KEY} FROM {BALANCE_TABLE} WHERE {USERID_KEY}=?', (from_userid,))
        from_balance = float(cursor.fetchone()[0])
        cursor.execute(f'SELECT {OVERDRAFT_LIMIT_KEY} FROM {USER_TABLE} WHERE {USERID_KEY}=?', (from_userid,))
        overdraft_limit = float(cursor.fetchone()[0])
        if from_balance + overdraft_limit < value:
            return False, 'Insufficient funds'
        
        timestamp = int(datetime.datetime.now().timestamp())
        guid = str(uuid.uuid4()) # guid is unique for user.
        cursor.execute(f'SELECT {BALANCE_KEY} FROM {BALANCE_TABLE} WHERE {USERID_KEY}=?', (to_userid,))
        to_balance = float(cursor.fetchone()[0])
        cursor.execute(f'UPDATE {BALANCE_TABLE} SET {BALANCE_KEY}=? WHERE {USERID_KEY}=?', (from_balance - value, from_userid))
        cursor.execute(f'UPDATE {BALANCE_TABLE} SET {BALANCE_KEY}=? WHERE {USERID_KEY}=?', (to_balance + value, to_userid))
        cursor.execute(f'''INSERT INTO {TRANACTIONS_TABLE} ({USERID_KEY}, {VALUE_KEY}, {TIMESTAMP_KEY}, {DESCRIPTION_KEY}, {ID_KEY}) 
                           VALUES (?, ?, ?, ?, ?)''', (from_userid, -value, timestamp, description, guid))
        cursor.execute(f'''INSERT INTO {TRANACTIONS_TABLE} ({USERID_KEY}, {VALUE_KEY}, {TIMESTAMP_KEY}, {DESCRIPTION_KEY}, {ID_KEY}) 
                           VALUES (?, ?, ?, ?, ?)''', (to_userid, value, timestamp, description, guid))
        conn.commit()
        conn.close()

        return True, None
    
    def get_user_transactions(self, userid: str, last_n: int, from_timestamp: int=None, to_timestamp: int=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        where_parts = filter(lambda x: x is not None, [
            f'{USERID_KEY}=?', 
            f'{TIMESTAMP_KEY}>={from_timestamp}' if from_timestamp is not None else None,
            f'{TIMESTAMP_KEY}<={to_timestamp}' if to_timestamp is not None else None
        ])

        limit_part = f'LIMIT {last_n}' if last_n is not None else ''

        cursor.execute(f'SELECT {TIMESTAMP_KEY}, {VALUE_KEY}, {DESCRIPTION_KEY}, {ID_KEY} FROM {TRANACTIONS_TABLE} ' +
                       f'WHERE {" AND ".join(where_parts)} ORDER BY {TIMESTAMP_KEY} DESC ' + 
                       limit_part , (userid,))
        res = cursor.fetchall()

        conn.close()
        return res
    
    def close(self):
        self.jobs_lock.drop()
        print("propery closing the database")

    def update_jobs(self):
        raise NotImplementedError()
