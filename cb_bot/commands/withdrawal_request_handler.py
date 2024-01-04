from enum import Enum
from typing import Callable

import discord

from cb_bot.commands.request_handler import RequestHandler
from cb_bot.common import get_printable_user_name, normalize_message
from cb_bot.user_info_provider import UserInfoProvider


class RequestStatus(Enum):
    PENDING_CONFIRMATION = 1
    COMPLETED = 100

class WithdrawalRequestHandler(RequestHandler):
    '''
    A request for a withdrawal 
    the user_id is the user to withdraw from
    the to_user_id is the user to transfer the money to
    '''
    CONFIRM_MSG = "Please confirm by typing **confirm**"

    def __init__(self, user_id: str, amount: float, to_user_id: str, description: str, user_info_provider: UserInfoProvider, 
                 complete:Callable):
        super().__init__(user_id)
        self.amount = amount
        self.to_user_id = to_user_id
        self.description = description
        self.user_info_provider = user_info_provider
        self.complete = complete

    async def initiate_interaction(self, channel: discord.channel) -> bool:
        to_user_info = self.user_info_provider.get_user_info(self.to_user_id)
        await channel.send(f"The user {get_printable_user_name(to_user_info)} is asking you  to withdraw **{self.amount}** from your account. with the following description:\n" + \
            f"`{self.description}`\n" + \
            WithdrawalRequestHandler.CONFIRM_MSG)
        return False

    async def handle_message(self, message: discord.Message) -> bool:
        print(f"handling message {message.content}")
        msg = normalize_message(message.content)
        if msg == 'confirm':
            response = await self.complete()
            await message.channel.send(response)
            return True
        
        await message.channel.send('Invalid input. ' + WithdrawalRequestHandler.CONFIRM_MSG)
        return False