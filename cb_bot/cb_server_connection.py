from collections import namedtuple
from typing import List
import aiohttp

from cb_bot.cb_user_mapper import UserMapper

class CBServerConnection:
    """Represents a connection to the CB backend server"""
    def __init__(self, server_url: str, mapper: UserMapper):
        self.server_url = server_url
        self.mapper = mapper

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