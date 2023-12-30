from collections import namedtuple
from typing import Callable
from discord.ext import commands

UserInfo = namedtuple('UserInfo', ['name', 'nickname', 'display_name', 'dm_channel'])
ExternalUserInfo = namedtuple('ExternalUserInfo', ['user_id', 'name', 'nickname', 'display_name', 'dm_channel' ])

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
                
                # create dm channel if needed
                if member.dm_channel is None:
                    await member.create_dm()
                # merge the updated info into the user dict
                user_dict = {**user_dict, 'name': member.name, 'nickname': member.global_name, 'display_name': member.display_name, 
                             'dm_channel': member.dm_channel}
                self.users[user_id] = UserInfo(**user_dict)

        register_task(update_users)

    def get_user_info(self, user_id: str) -> ExternalUserInfo:
        return ExternalUserInfo(user_id = user_id, **self.users[user_id]._asdict())

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
    
    def get_all_users(self) -> list[ExternalUserInfo]:
        return [self.get_user_info(k) for k in self.users.keys()]

