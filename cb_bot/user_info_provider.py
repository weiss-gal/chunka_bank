from collections import namedtuple
from typing import Callable
from discord.ext import commands

UserInfo = namedtuple('UserInfo', ['name', 'nickname', 'display_name' ])

class UserInfoProvider:

    def __init__(self, bot: commands.Bot, register_task: Callable):
        self.bot = bot
        self.users: dict[str, UserInfo] = {}

        async def update_users():
            for member in self.bot.get_all_members():
                if member.bot:
                    continue

                user_id = str(member.id)
                user_dict = {}
                if user_id in self.users:
                    user_dict = self.users[user_id]._asdict()
                
                # merge the updated info into the user dict
                user_dict = {**user_dict, 'name': member.name, 'nickname': member.global_name, 'display_name': member.display_name}
                self.users[user_id] = UserInfo(**user_dict)

        register_task(update_users)

    def get_user_info(self, user_id: str) -> UserInfo:
        return self.users[user_id]

    def search_user(self, search_str: str) -> str:
        print("Searching for user: ", search_str) # XXX debug
        for user_key in self.users.keys():
            user_info = self.users[user_key]
            search_str = search_str.lower()
            if user_info.name.lower().startswith(search_str) or user_info.nickname.lower().startswith(search_str) \
                or user_info.display_name.lower().startswith(search_str):
                print("Found user: ", user_info) # XXX debug
                return user_key
        
        return None
    
    def get_all_users(self) -> list[UserInfo]:
        return [self.users[k] for k in self.users.keys()]

    


