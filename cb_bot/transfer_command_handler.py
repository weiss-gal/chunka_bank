from enum import Enum
from typing import List
import discord
import re

from cb_bot.cb_server_connection import CBServerException
from .command_handler import CommandHandler
from .command_utils import CommandUtils
class CommandStatus(Enum):
    START = 0
    PENDING_CONFIRMATION = 1
    COMPLETED = 100

class TransferCommandHandler(CommandHandler):
    """
    Handle the transfer command
    The following formats are supported:
    - transfer 
    - transfer <amount> to <username> [description]
    """
    PHRASE = 'transfer'
    FORMAT = f'{PHRASE} <amount> to <username> [description]'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = CommandStatus.START
        self.amount = None
        self.to = None
        self.description = None

    def matches(message: str) -> bool:
        return CommandUtils.split_message(message)[0] == TransferCommandHandler.PHRASE
    
    def get_phrase() -> str:
        return TransferCommandHandler.PHRASE
    
    def resolve_user_id(self, user_str: str) -> str:
        return self.user_info_provider.search_user(user_str)

    def handle_full_command(self, command_parts: List[str]) -> str:
        """
        Parse the full command, return True if the command is valid, False otherwise
        If the command is invalid, the error message is returned as well
        """
        invalid_format = 'Invalid command format, use:\n' + \
            f'  `{TransferCommandHandler.FORMAT}`'

        # anyting from the 5th part is considered description
        if len(command_parts) < 4:
            self.status = CommandStatus.COMPLETED
            return invalid_format
        
        # parse amount
        try:
            self.amount = float(command_parts[1])
            if self.amount <= 0:
                self.status = CommandStatus.COMPLETED
                return f'Invalid amount: \'{command_parts[1]}\', must be positive'
        except ValueError:
            self.status = CommandStatus.COMPLETED
            return f'Invalid amount: \'{command_parts[1]}\''
        
        self.amount = float(command_parts[1])
        
        # parse to
        if command_parts[2] != 'to':
            self.status = CommandStatus.COMPLETED
            return invalid_format
    
        to_str = command_parts[3]
        self.to = self.resolve_user_id(to_str)    
        if self.to == self.user_id:
            self.status = CommandStatus.COMPLETED
            return f'You cannot transfer money to yourself'
        if not self.to:
            self.status = CommandStatus.COMPLETED
            return f'User \'{to_str}\' not found, please type one of the following users (or part of their name):\n' + \
                f'{"\n".join([f"  {user.name}: {user.display_name}" for user in self.user_info_provider.get_all_users()])}'
        
        # parse description
        if len(command_parts) > 4:
            # remove heading or trailing double/single quotes
            self.description = re.sub(r'''^['"]?|['"]$''', '', ' '.join(command_parts[4:])).strip()
        else:
            self.description = f"Transfer {self.amount} from '{self.user_info_provider.get_user_info(self.user_id).display_name}' " + \
                f"to '{self.user_info_provider.get_user_info(self.to).display_name}'"
        self.status = CommandStatus.PENDING_CONFIRMATION
        return f"You are about to transfer {self.amount} to **{self.user_info_provider.get_user_info(self.to).display_name}** " + \
            f"with description\n`{self.description}`\n" + \
            f"Please confirm by typing *yes* or *y*"

    async def handle_confirmation(self, command_parts: List[str]) -> str:
        if len(command_parts) != 1 or command_parts[0].lower() not in ['yes', 'y']:
            return f"Invalid confirmation format, please type *yes* or *y*"
        
        self.status = CommandStatus.COMPLETED
        # transfer the money
        try:
            await self.server_connection.do_money_transfer(self.user_id, self.to, self.amount, self.description)
        except CBServerException as e:
            return f"Failed to transfer money: [{e.server_error.error_code}]{e.server_error.error_msg}"
        
        return None # no need for report, notifications are sent automatically.
    
    async def handle_message(self, message: discord.Message) -> bool:
        command_parts = CommandUtils.split_message(message.content)
        
        response = None
        if self.status == CommandStatus.START:
            if len(command_parts) == 1:
                await message.channel.send(f'Please use the following format:\n  `{TransferCommandHandler.FORMAT}`')
                return True
            response = self.handle_full_command(command_parts)
        elif self.status == CommandStatus.PENDING_CONFIRMATION:
            response = await self.handle_confirmation(command_parts)
        else:
            raise Exception(f'Invalid status: {self.status}. This should not happen')

        if response: await message.channel.send(response)
        return self.status == CommandStatus.COMPLETED