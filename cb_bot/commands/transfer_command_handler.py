from datetime import datetime
from enum import Enum
from typing import List
import discord
import re

from cb_bot.cb_server_connection import CBServerException
from cb_bot.commands.command_exception import CommandParamException
from cb_bot.common import get_printable_user_name
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
        self.channel: discord.channel = None
        self.last_activity: datetime = None

    def matches(message: str) -> bool:
        return CommandUtils.split_message(message)[0] == TransferCommandHandler.PHRASE
    
    def get_prefix() -> str:
        return TransferCommandHandler.PHRASE
    
    def resolve_user_id(self, user_str: str) -> str:
        return self.user_info_provider.search_user(user_str)
    
    def get_default_description(self) -> str:
        return f"Transfer {self.amount} from '{self.user_info_provider.get_user_info(self.user_id).display_name}' " + \
                f"to '{self.user_info_provider.get_user_info(self.to).display_name}'"

    def handle_full_command(self, command_parts: List[str]) -> str:
        """
        Parse the full command, return True if the command is valid, False otherwise
        If the command is invalid, the error message is returned as well
        """
        invalid_format = 'Invalid command format, use:\n' + \
            f'  `{type(self).FORMAT}`'

        # anyting from the 5th part is considered description
        if len(command_parts) < 4:
            self.status = CommandStatus.COMPLETED
            return invalid_format
        
        # parse amount
        try:
            self.amount = CommandUtils.parse_amount(command_parts[1], 1)
        except CommandParamException as e:
            self.status = CommandStatus.COMPLETED
            return CommandUtils.get_param_error_msg(e, command_parts)
        
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
            users_list = "\n".join(["  " + get_printable_user_name(user) for user in self.user_info_provider.get_all_users()])
            return f'User \'{to_str}\' not found, please type one of the following users (or part of their name):\n' + \
                    users_list
        
        # parse description
        if len(command_parts) > 4:
            # remove heading or trailing double/single quotes
            self.description = re.sub(r'''^['"]?|['"]$''', '', ' '.join(command_parts[4:])).strip()
        else:
            self.description = self.get_default_description()

        self.status = CommandStatus.PENDING_CONFIRMATION
        return f"You are about to transfer {self.amount} to **{self.user_info_provider.get_user_info(self.to).display_name}** " + \
            f"with description\n`{self.description}`\n" + \
            f"Please confirm by typing *yes* or *y*"

    async def confirmed(self) -> str:
        self.status = CommandStatus.COMPLETED
        # transfer the money
        try:
            await self.server_connection.do_money_transfer(self.user_id, self.to, self.amount, self.description)
        except CBServerException as e:
            return f"Failed to transfer money: [{e.server_error.error_code}]{e.server_error.error_msg}"
        
        return 'Money transfered successfully'
    
    async def cancelled(self) -> str:
        self.status = CommandStatus.COMPLETED
        return 'Transfer cancelled'
        
    async def handle_message(self, message: discord.Message) -> bool:
        self.last_activity = datetime.now()
        self.channel = message.channel
        command_parts = CommandUtils.split_message(message.content)
        
        response = None
        if self.status == CommandStatus.START:
            if len(command_parts) == 1:
                await message.channel.send(f'Please use the following format:\n  `{type(self).FORMAT}`')
                return True
            response = self.handle_full_command(command_parts)
        elif self.status == CommandStatus.PENDING_CONFIRMATION:
            response = await CommandUtils.handle_confirmation(command_parts, self.cancelled, self.confirmed)
        else:
            raise Exception(f'Invalid status: {self.status}. This should not happen')

        if response: await message.channel.send(response)
        return self.status == CommandStatus.COMPLETED

    async def check_expired(self) -> bool:        
        if self.status == CommandStatus.PENDING_CONFIRMATION and \
            (datetime.now() - self.last_activity).total_seconds() > type(self).TIMEOUT_S:
            await self.channel.send(CommandUtils.get_expired_msg())
            return True
        
        return False
        
