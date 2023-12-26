from collections import namedtuple
from typing import Callable
from discord.ext import commands

from cb_bot.dialog import Dialog

UserInfo = namedtuple('UserInfo', ['dialogs', 'name', 'nickname', 'display_name' ])

class UserManager:

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
        for user_key in self.users.keys():
            user_info = self.users[user_key]
            search_str = search_str.lower()
            if user_info.name.lower().starswith(search_str) or user_info.nickname.lower().starswith(search_str) \
                or user_info.display_name.lower().starswith(search_str):
                return user_key
        
        return None

    def get_user_dialog(self, user_id: str, channel_id: str) -> Dialog:
        if user_id not in self.users:
            return None
        
        user_info = self.users[user_id]
        return user_info.dialogs.get(channel_id)
        
    def set_user_dialog(self, user_id: str, channel_id: str, dialog: Dialog):
        if user_id not in self.users:
            self.users[user_id] = UserInfo(None, {})
        
        user_info = self.users[user_id]
        if channel_id in user_info.dialogs:
            raise Exception(f'User {user_id} already has a dialog in channel {channel_id}')

        user_info.dialogs[channel_id] = dialog

    def unset_user_dialog(self, user_id: str, channel_id: str):
        user_info = self.users[user_id]

        del user_info.dialogs[channel_id]

    


