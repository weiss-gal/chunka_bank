from collections import namedtuple
from typing import List
import aiohttp
import discord

from cb_bot.cb_user_mapper import UserMapper

UserInfo = namedtuple('UserInfo', ['discord_user_id', 'name', 'global_name'])

class CBServerConnection:
    """Represents a connection to the CB backend server"""
    def __init__(self, server_url: str, mapper: UserMapper):
        self.server_url = server_url
        self.mapper = mapper
        self.user_list = None

    def update_users(self, users: List[discord.User]):
        """Updates the user map with the given list of discord users"""
        print(f'Updating user list with users: {users}')
        new_user_list = []
        for user in users:
            if user.bot:
                continue
            new_user_list.append(UserInfo(discord_user_id=user.id, name=user.name, global_name=user.global_name))
        print(f'New user list: {new_user_list}') # XXX debug
        self.user_list = new_user_list

    def find_discord_user(self, username_prefix: str) -> List[str]:
        """Returns a list of discord user ids that match the given username prefix"""
        return [u.discord_user_id for u in self.user_list if u.name.startswith(username_prefix)]

    async def get_user_balance(self, user_id: str):
        cb_user_id = self.mapper.get_cb_user_id(user_id)
        if cb_user_id is None:
            raise Exception(f'Chunka Bank {user_id} not found in mapper')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.server_url}/user/{cb_user_id}/balance') as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    return float(resp_json['balance'])
                elif resp.status == 404:
                    return None
                else:
                    raise Exception(f'Unexpected status code: {resp.status}')