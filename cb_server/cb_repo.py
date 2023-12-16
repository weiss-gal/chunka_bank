import sqlite3

BALANCE_TABLE = 'user_balance'
USER_TABLE = 'user'

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
                userid TEXT PRIMARY KEY,
                balance REAL
            )
        ''')
        # Create the 'user' table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {USER_TABLE} (
                userid TEXT PRIMARY KEY
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
        cursor.execute(f'SELECT balance FROM {BALANCE_TABLE} WHERE userid=?', (userid,))
        res = cursor.fetchone()
        if res is None:
            raise UserNotFound(f"User '{userid}' not found")
        
        return res[0]
    
    def add_user(self, userid):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'INSERT INTO {BALANCE_TABLE} (userid, balance) VALUES (?, ?)', (userid, 0))
    
