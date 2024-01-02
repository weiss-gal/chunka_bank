'''
Abstract class for a Request
Request is a special type of interaction that is not initiated by the user, but rather by the bot itself
It may be a one time notification, or a request for a response from the user
'''
from enum import Enum
from typing import Callable
import discord
from cb_bot.commands.interaction_handler import InteractionHandler
from cb_bot.common import normalize_message

class RequestHandler(InteractionHandler):
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def get_userid(self):
        return self.user_id

    # returns true if the command handling is completed
    async def initiate_interaction(self, channel: discord.channel) -> bool:
        raise NotImplementedError

    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError

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

    def __init__(self, user_id: str, amount: float, to_user_id: str, description: str, complete:Callable):
        super().__init__(user_id)
        self.amount = amount
        self.to_user_id = to_user_id
        self.description = description
        self.complete = complete

    async def initiate_interaction(self, channel: discord.channel) -> bool:
        await channel.send(f"You are about to withdraw **{self.amount}** with the following description:\n" + \
            f"`{self.description}`\n" + \
            WithdrawalRequestHandler.CONFIRM_MSG)
        return False

    async def handle_message(self, message: discord.Message) -> bool:
        msg = normalize_message(message.content)
        if msg == 'confirm':
            response = await self.complete()
            await message.channel.send(response)
            return True
        
        await message.channel.send('Invalid input. ' + WithdrawalRequestHandler.CONFIRM_MSG)
        return False