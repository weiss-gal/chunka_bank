import re
from typing import Any, Callable, Coroutine, List
from discord import Enum, Message
import discord
from cb_bot.cb_server_connection import CBServerConnection, CBServerException
from cb_bot.cb_user_mapper import UserMappingInfo
from cb_bot.commands.command_exception import CommandFormatException, CommandParamException
from cb_bot.commands.command_handler import CommandHandler
from cb_bot.commands.command_utils import CommandUtils
from cb_bot.commands.notification_handler import NotificationHandler
from cb_bot.commands.request_handler import WithdrawalRequestHandler
from cb_bot.common import get_printable_user_name
from cb_bot.user_info_provider import UserInfoProvider

class CommandStatus(Enum):
    START = 1
    PENDING_CONFIRMATION = 2
    COMPLETED = 100

class WithdrawCommandHandler(CommandHandler):
    """
    Command handler for 'request withdraw' command
    - the following formats are supported:
        - request withdraw <amount> from <username> [description]
        - request withdraw
    """
    PREFIX = "request withdraw"
    PREFIX_LEN = len(PREFIX.split())

    def matches(message: str) -> bool:
        return message.startswith(WithdrawCommandHandler.PREFIX)
    
    def get_prefix() -> str:
        return WithdrawCommandHandler.PREFIX

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = CommandStatus.START
        self.amount = None
        self.request_from = None 

    '''this function is called after the other party confirmed the request'''   
    async def other_party_confirmed(self) -> str:
        # notify the user that the request has been approved
        notification = f"The user {get_printable_user_name(self.user_info_provider.get_user_info(self.request_from))} " + \
            f"has approved your withdraw request of {self.amount}"
        approval_notification = NotificationHandler(self.user_id, notification)
        self.queue_interaction(self.user_id, approval_notification)

        # send request to server
        try:
            await self.server_connection.do_money_transfer(self.request_from, self.user_id, self.amount, self.description)
        except CBServerException as e:
             return f"Failed to withdraw money: [{e.server_error.error_code}]{e.server_error.error_msg}"
        
        return 'Money withdrawed successfully'

    async def confirmed(self) -> str:
        self.status = CommandStatus.COMPLETED
        # TODO: send request to other user
        self.queue_interaction(self.request_from, WithdrawalRequestHandler(self.user_id, self.amount, self.request_from, self.description, self.other_party_confirmed))
        from_user_info = self.user_info_provider.get_user_info(self.request_from)
        return f"Withdraw request has been sent to {get_printable_user_name(from_user_info)} for approval, you will be notified when it is approved"

    def get_default_description(self) -> str:
        return f"Withdraw {self.amount} by {get_printable_user_name(self.user_info_provider.get_user_info(self.request_from), False)}"

    def resolve_user_id(self, user_str: str) -> str:
        return self.user_info_provider.search_user(user_str)

    def handle_full_command(self, command_parts: List[str]) -> str:
        self.amount = CommandUtils.parse_amount(command_parts[2], 2)
        if command_parts[3] != "from":
            raise CommandParamException("Expected 'from' keyword", 3)
        
        self.request_from = self.resolve_user_id(command_parts[4])    
        if self.request_from == self.user_id:
            raise CommandParamException('You cannot transfer money to yourself', 4)
        if not self.request_from:
            raise CommandParamException(f'User \'{command_parts[4]}\' not found, please type one of the following users (or part of their name):\n' + \
                f'{"\n".join(["  " + get_printable_user_name(user) for user in self.user_info_provider.get_all_users()])}', 4)
        
        if len(command_parts) > 5:
            # remove heading or trailing double/single quotes
            self.description = re.sub(r'''^['"]?|['"]$''', '', ' '.join(command_parts[5:])).strip()
        else:
            self.description = self.get_default_description()

        self.status = CommandStatus.PENDING_CONFIRMATION
        from_user_name = get_printable_user_name(self.user_info_provider.get_user_info(self.request_from))
        return f"You are about to request the user {from_user_name} to confirm a withdrawal of {self.amount} " + \
            f"with description\n`{self.description}`\n" + \
            f"Please confirm by typing *yes* or *y*"

    async def handle_message(self, message: discord.Message) -> bool:
        format = f'`{WithdrawCommandHandler.PREFIX} <amount> from <username> [description]`'
        command_parts = CommandUtils.split_message(message.content)

        response = None
        if self.status == CommandStatus.START:
            try:
                if len(command_parts) < type(self).PREFIX_LEN + 3:
                    raise CommandFormatException()
                
                response = self.handle_full_command(command_parts)
            except CommandFormatException as e:
                self.status = CommandStatus.COMPLETED
                response = f'Invalid command format, use:\n' + format
            except CommandParamException as e:
                self.status = CommandStatus.COMPLETED
                response = CommandUtils.get_param_error_msg(e, command_parts)
                
        elif self.status == CommandStatus.PENDING_CONFIRMATION:
            response = await CommandUtils.handle_confirmation(command_parts, self.confirmed)

        await message.channel.send(response)
        return self.status == CommandStatus.COMPLETED

    def is_allowed(user_mapping_info: UserMappingInfo) -> bool:
        return user_mapping_info.is_admin