import sqlite3

BALANCE_TABLE = 'user_balance'
USER_TABLE = 'user'

class RepoException(Exception):
    pass

class UserNotFound(RepoException):
    pass

class Repo:
    def __init__(self, db_path):
        self.db_path = db_path

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
    
