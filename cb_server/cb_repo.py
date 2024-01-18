import datetime
import functools
import inspect
import sqlite3
import uuid

REQUIRED_DB_VERSION = 1

BALANCE_TABLE = 'user_balance'
USER_TABLE = 'user'
TRANACTIONS_TABLE = 'transactions'
VERSION_TABLE = 'version'
#JOBS_TABLE = 'jobs'

USERID_KEY = 'userid'
BALANCE_KEY = 'balance'
OVERDRAFT_LIMIT_KEY = 'overdraft_limit'
VALUE_KEY = 'value'
TIMESTAMP_KEY = 'timestamp'
DESCRIPTION_KEY = 'description'
ID_KEY = 'id'
VERSION_KEY = 'version'
#CRON_KEY = 'cron'

class RepoException(Exception):
    pass

class UserNotFound(RepoException):
    pass

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
        res = cursor.fetchone()
        if res is None:
            raise Exception(f"Database version table '{VERSION_TABLE}' exists but has no version")
        
        version = res[0]
        return version
    
    def create_version_table(self, conn: sqlite3.Connection=None, version:int=REQUIRED_DB_VERSION):
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {VERSION_TABLE} (
                {VERSION_KEY} INTEGER NOT NULL
            )
        ''')
        cursor.execute(f'INSERT INTO {VERSION_TABLE} ({VERSION_KEY}) VALUES ({version})')
        cursor.close()

    def backward_compatibility(self):
        # get database version
        conn = sqlite3.connect(self.db_path)
        db_version = self.get_database_version(conn=conn)
        print(f'Database version: {db_version}')
        while db_version < REQUIRED_DB_VERSION:
            if db_version == 0:
                print("Upgrading database from version 0 to 1")
                # create the 'version' table. explicitly set the version to 1
                self.create_version_table(conn, 1)
                
            # we commit after each version upgrade
            conn.commit()   
            db_version = self.get_database_version()

        conn.close()
        print(f"Database migration completed. Database is up to date ({db_version})")

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
        conn.commit()
        conn.close()

    def __init__(self, db_path: str, create: bool=False):
        self.db_path = db_path
        if create:
            self.create_database()
        else:
            self.backward_compatibility()
        
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
    
    def update_jobs(self):
        raise NotImplementedError()
