import datetime
import sqlite3

BALANCE_TABLE = 'user_balance'
USER_TABLE = 'user'
TRANACTIONS_TABLE = 'transactions'

USERID_KEY = 'userid'
BALANCE_KEY = 'balance'
OVERDRAFT_LIMIT_KEY = 'overdraft_limit'
VALUE_KEY = 'value'
TIMESTAMP_KEY = 'timestamp'
DESCRIPTION_KEY = 'description'

class RepoException(Exception):
    pass

class UserNotFound(RepoException):
    pass

class Repo:
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
                {DESCRIPTION_KEY} TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def __init__(self, db_path: str, create: bool=False):
        self.db_path = db_path
        if create:
            self.create_database()
        
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
        cursor.execute(f'SELECT {BALANCE_KEY} FROM {BALANCE_TABLE} WHERE {USERID_KEY}=?', (to_userid,))
        to_balance = float(cursor.fetchone()[0])
        cursor.execute(f'UPDATE {BALANCE_TABLE} SET {BALANCE_KEY}=? WHERE {USERID_KEY}=?', (from_balance - value, from_userid))
        cursor.execute(f'UPDATE {BALANCE_TABLE} SET {BALANCE_KEY}=? WHERE {USERID_KEY}=?', (to_balance + value, to_userid))
        cursor.execute(f'''INSERT INTO {TRANACTIONS_TABLE} ({USERID_KEY}, {VALUE_KEY}, {TIMESTAMP_KEY}, {DESCRIPTION_KEY}) 
                           VALUES (?, ?, ?, ?)''', (from_userid, -value, timestamp, description))
        cursor.execute(f'''INSERT INTO {TRANACTIONS_TABLE} ({USERID_KEY}, {VALUE_KEY}, {TIMESTAMP_KEY}, {DESCRIPTION_KEY}) 
                           VALUES (?, ?, ?, ?)''', (to_userid, value, timestamp, description))
        conn.commit()
        conn.close()

        return True, None
