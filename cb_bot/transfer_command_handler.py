from enum import Enum
from typing import List, Tuple
import discord

from cb_bot.cb_server_connection import CBServerConnection
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
        return self.user_manager.search_user(user_str)

    def parse_full_command(self, command_parts: List[str]) -> str:
        """
        Parse the full command, return True if the command is valid, False otherwise
        If the command is invalid, the error message is returned as well
        """
        invalid_format = 'Invalid command format, use:\n' + \
            f'  `{TransferCommandHandler.FORMAT}`'

        if len(command_parts) not in [4, 5]:
            self.status = CommandStatus.COMPLETED
            return invalid_format
        
        # parse amount
        try:
            self.amount = float(command_parts[1])
            if self.amount <= 0:
                self.status = CommandStatus.COMPLETED
                return f'Invalid amount \'{command_parts[1]}\', must be positive'
        except ValueError:
            self.status = CommandStatus.COMPLETED
            return f'Invalid amount \'{command_parts[1]}\''
        
        self.amount = float(command_parts[1])
        
        # parse to
        if command_parts[2] != 'to':
            self.status = CommandStatus.COMPLETED
            return invalid_format
    
        to_str = command_parts[3]
        self.to = self.resolve_user_id(to_str)    
        
        # parse description
        self.description = ' '.join(command_parts[4:])
        
        return True, ''

    async def handle_message(self, message: discord.Message) -> bool:
        command_parts = CommandUtils.split_message(message.content)
        if len(command_parts) == 1:
            await message.channel.send(f'Please use the following format:\n' +
                                        f'  `{TransferCommandHandler.FORMAT}`')
            return True
            
        response = self.parse_full_command(command_parts)    
        message.channel.send(response)
        return self.status == CommandStatus.COMPLETED