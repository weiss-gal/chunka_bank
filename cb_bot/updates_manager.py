import datetime
import logging
from typing import Callable, Dict, Tuple, Set
from cb_bot.cb_server_connection import CBServerConnection, CBServerNoUserException
from cb_bot.user_info_provider import UserInfoProvider

class UpdatesManager:
    def refresh_users(self):
        all_users = self.user_info_provider.get_all_users()
        print("all users: ", all_users)
        for user_info in all_users:
            if user_info.user_id not in self.last_update:
                logging.info(f"Adding user {user_info.user_id} to updates manager")
                self.last_update[user_info.user_id] = datetime.datetime.now().timestamp(), set()
        
        for user_id in set(self.last_update.keys()):
            if user_id not in {u.user_id for u in all_users}:
                logging.info(f"Removing user {user_id} from updates manager")
                del self.last_update[user_id]

    async def poll_updates(self):
        self.refresh_users()
        for user_id in self.last_update.keys():
            last_update, transaction_ids = self.last_update[user_id]
            # get all transactions since the last update
            try:
                transactions = await self.cb_server_connection.get_user_transactions(user_id, from_timestamp=last_update)
            except CBServerNoUserException as e:
                # This is actually a valid use case when a user is added to the discord server but does not have mapping to a CB user yet
                logging.warning(f"Failed to get transactions for user {user_id}")
                continue

            for transaction in transactions:
                if transaction.id in transaction_ids:
                    continue

                print(f"New transaction for user {user_id}: {transaction}")

    def __init__(self, cb_server_connection: CBServerConnection, user_info_provider: UserInfoProvider, register_task: Callable):
        self.cb_server_connection: CBServerConnection = cb_server_connection
        self.user_info_provider: UserInfoProvider = user_info_provider
        # mapping from user id to last update timestamp and a set of the last transactions ids
        # the latter part is required because we can't rely on the timestamp alone, since timestamp 
        # resolution is 1 second and we can have multiple transactions in the same second
        self.last_update: Dict[str, Tuple[int, Set[str]]] = {}
        self.refresh_users()
    
        register_task(self.poll_updates)
