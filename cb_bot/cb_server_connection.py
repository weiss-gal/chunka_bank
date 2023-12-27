from collections import namedtuple
from typing import List
import aiohttp

from cb_bot.cb_user_mapper import UserMapper
from models.server_errors import ServerError

class CBServerException(Exception):
    def __init__(self, server_error: ServerError):
        print("server_error type is: ", type(server_error))
        self.server_error = server_error

class CBServerConnection:
    """Represents a connection to the CB backend server"""
    def __init__(self, server_url: str, mapper: UserMapper):
        self.server_url = server_url
        self.mapper = mapper

    async def get_server_exception(self, resp: aiohttp.ClientResponse):
        resp_json = await resp.json()
        return CBServerException(ServerError(**resp_json))

    async def do_money_transfer(self, from_user_id: str, to_user_id: str, amount: float, description=None):
        cb_from_user_id = self.mapper.get_cb_user_id(from_user_id)
        cb_to_user_id = self.mapper.get_cb_user_id(to_user_id)
        if cb_from_user_id is None:
            raise Exception(f'Chunka Bank {from_user_id} not found in mapper')
        if cb_to_user_id is None:
            raise Exception(f'Chunka Bank {to_user_id} not found in mapper')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.server_url}/user/{cb_from_user_id}/transfer', json={
                'to': cb_to_user_id,
                'value': amount,
                'description': description
            }) as resp:
                if resp.status == 204:
                    return
                
                raise await self.get_server_exception(resp)
    

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