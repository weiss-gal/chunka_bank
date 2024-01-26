from enum import Enum
import sqlite3

LOCKS_TABLE = 'locks'

LOCK_TYPE_KEY = 'type'
LOCKED_KEY = 'locked'

class LockType(Enum):
    JOBS = 'jobs'

class JobsLock:
    """
    Locks the jobs processing so only one instance of the job processor is running at a time.
    """
    def take_lock(self):
        # check if the lock table exists
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{LOCKS_TABLE}'")
        if len(c.fetchall()) == 0:
            # the table does not exist, create it
            c.execute(f"CREATE TABLE {LOCKS_TABLE} ({LOCK_TYPE_KEY} TEXT, {LOCKED_KEY} INTEGER)")

        # check if the lock is taken
        c.execute(f"SELECT {LOCKED_KEY} FROM {LOCKS_TABLE} WHERE {LOCK_TYPE_KEY}='{LockType.JOBS.value}'")
        res = c.fetchall()
        if len(res) > 1:
            # multiple locks found, abort
            raise Exception("Multiple jobs locks found, something is wrong with the database")
        
        if len(res) == 0:
            # the lock is not taken, take it
            c.execute(f"INSERT INTO {LOCKS_TABLE} VALUES ('{LockType.JOBS.value}', 1)")
        elif res[0][0] == 0:
            # the lock is not taken, take it
            c.execute(f"UPDATE {LOCKS_TABLE} SET {LOCKED_KEY}=1 WHERE {LOCK_TYPE_KEY}='{LockType.JOBS.value}'")
        else:
            # the lock is taken, abort
            raise Exception("The jobs lock is already taken")
        
        c.close()
        conn.commit()

    def drop_lock(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(f"UPDATE {LOCKS_TABLE} SET {LOCKED_KEY}=0 WHERE {LOCK_TYPE_KEY}='{LockType.JOBS.value}'")
        c.close()
        conn.commit()

    def __init__(self, db_path: str):
        self.db_path = db_path
    
        self.is_locked = True
        self.take_lock()

    def drop(self):
        if not self.is_locked:
            raise Exception("Multiple attempts to drop the jobs lock detected")
        
        self.drop_lock()
        self.is_locked = False
