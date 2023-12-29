from collections import namedtuple
from datetime import datetime, timezone
from typing import List
import aiohttp

from cb_bot.cb_user_mapper import UserMapper
from models.server_errors import ErrorCodes, ServerError
from models.transactions import UserTransactionInfo

class CBServerException(Exception):
    def __init__(self, server_error: ServerError):
        self.server_error = server_error

class CBServerNoUserException(CBServerException):
    def __init__(self, user_id: str):
        super().__init__(self, ServerError(error_code=ErrorCodes.INTERNAL_ERROR, error_msg=f"User '{user_id}' not found on CB server"))

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
            raise CBServerNoUserException(from_user_id)
        if cb_to_user_id is None:
            raise CBServerNoUserException(to_user_id)
        
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
            raise CBServerNoUserException(user_id)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.server_url}/user/{cb_user_id}/balance') as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    return float(resp_json['balance'])
                elif resp.status == 404:
                    return None
                else:
                    raise Exception(f'Unexpected status code: {resp.status}') 

    async def get_user_transactions(self, user_id: str, from_timestamp: int = None, to_timestamp: int = None) -> List[UserTransactionInfo]:
        cb_user_id = self.mapper.get_cb_user_id(user_id)
        if cb_user_id is None:
            raise CBServerNoUserException(user_id)
        
        async with aiohttp.ClientSession() as session:
            query_params = {}
            if from_timestamp is not None:
                query_params['from_time'] = datetime.fromtimestamp(from_timestamp, tz=timezone.utc).isoformat()
            if to_timestamp is not None:
                query_params['to_time'] = datetime.fromtimestamp(to_timestamp, tz=timezone.utc).isoformat()

            print(f'query_params: {query_params}')
            async with session.get(f'{self.server_url}/user/{cb_user_id}/transactions', params=query_params) as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    print(f'got transactions: [{type(resp_json)}]{resp_json}')
                    return [UserTransactionInfo(**t) for t in resp_json]
                    
                if resp.status == 404:
                    return None
                
                raise Exception(f'Unexpected status code: {resp.status}')