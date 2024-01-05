from datetime import datetime
from enum import Enum
from typing import Callable

import discord
from cb_bot.commands.command_utils import CommandUtils

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
    CONFIRM_MSG = "Please confirm by typing **yes** or **y**"

    def __init__(self, user_id: str, amount: float, to_user_id: str, description: str, user_info_provider: UserInfoProvider, 
                 on_complete: Callable):
        super().__init__(user_id)
        self.amount = amount
        self.to_user_id = to_user_id
        self.description = description
        self.user_info_provider = user_info_provider
        self.on_complete = on_complete
        self.status = RequestStatus.PENDING_CONFIRMATION
        self.channel: discord.channel = None
        self.last_activity: datetime = None
        # the timeout is longer for the initial request since the user may not notice it
        self.timeout_s: float = type(self).TIMEOUT_S * 20 

    async def initiate_interaction(self, channel: discord.channel) -> bool:
        self.channel = channel
        self.last_activity = datetime.now()
        to_user_info = self.user_info_provider.get_user_info(self.to_user_id)
        await channel.send(f"The user {get_printable_user_name(to_user_info)} is asking you  to withdraw **{self.amount}** from your account. with the following description:\n" + \
            f"`{self.description}`\n" + \
            WithdrawalRequestHandler.CONFIRM_MSG)
        return False
    
    async def completed(self, is_confirmed: bool) -> str:
        response = await self.on_complete(is_confirmed)
        self.status = RequestStatus.COMPLETED
        return response

    async def handle_message(self, message: discord.Message) -> bool:
        self.last_activity = datetime.now()
        # after the initial request, the timeout is shorter
        self.timeout_s = type(self).TIMEOUT_S 
        msg_parts = CommandUtils.split_message(normalize_message(message.content))
        
        response = await CommandUtils.handle_confirmation(msg_parts, lambda: self.completed(False), lambda: self.completed(True))
        await message.channel.send(response)
        return self.status == RequestStatus.COMPLETED
    
    async def check_expired(self) -> bool:
        if self.status == RequestStatus.PENDING_CONFIRMATION and \
            (datetime.now() - self.last_activity).total_seconds() > self.timeout_s:
            await self.completed(False)
            await self.channel.send(CommandUtils.get_expired_msg())
            self.status = RequestStatus.COMPLETED
            return True
        
        return False