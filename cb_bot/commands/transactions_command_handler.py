from datetime import datetime
from typing import List
import discord
from cb_bot.cb_server_connection import CBServerConnection

from cb_bot.commands.command_utils import CommandUtils
from cb_bot.user_info_provider import UserInfoProvider
from .command_handler import CommandHandler

class CommandFormatException(Exception):
    pass

class CommandParamException(Exception):
    def __init__(self, msg: str, context=None):
        super().__init__(msg)
        self.context = context # any object that can be used to provide context for the error
    pass

class TransactionsCommandHandler(CommandHandler):
    """
    Handle the show transactions command
    The following formats are supported: 
    - show transactions last <n>
    - show transactions [from <date>] [to <date>]
      - date formats: 
        - DD-MMM-YY[YY]
        - DD/MM/YY[YY]
        - DD-MM-YY[YY]
    """
    PREFIX = 'show transactions'
    FORMATS = [
        f'{PREFIX} last <n>',
        f'{PREFIX} [from <date>] [to <date>]'
    ]
    
    def matches(message: str) -> bool:
        return message.startswith(TransactionsCommandHandler.PREFIX)
    
    def get_prefix() -> str:
        return TransactionsCommandHandler.PREFIX
    
    def __init__(self, user_id, channel_id, server_connection: CBServerConnection, user_info_provider: UserInfoProvider):
        super().__init__(user_id, channel_id, server_connection, user_info_provider)
        self.last_n = None
        self.from_date = None
        self.to_date = None
    
    async def parse_date(self, date_str: str, context) -> int:
        formats = [
            '%d-%b-%y',
            '%d-%b-%Y',
            '%d/%b/%y',
            '%d/%b/%Y',
            '%d-%m-%y',
            '%d-%m-%Y',
            '%d/%m/%y',
            '%d/%m/%Y',
        ]
        for f in formats:
            try:
                return int(datetime.strptime(date_str, f).timestamp())
            except ValueError:
                pass # try the next format

        formats_example = f'{", ".join(set([datetime.strftime(datetime.now(), f) for f in formats]))}'
        raise CommandParamException('invalid date format, use one of the following formats: ' + formats_example, context)

    async def parse_num(self, num_str: str, context) -> int:
        try:
            num = int(num_str)
            if num <= 0:
                raise CommandParamException('must be positive', context)
            return num
        except ValueError:
            raise CommandParamException('invalid number', context)

    async def handle_full_command(self, message: discord.Message, command_parts: List[str], element_offset) -> bool:
        parts = [p for p in command_parts] # deep copy
        while len(parts) > 0:
            if len(parts) < 2:
                raise CommandFormatException()
            
            if parts[0] == 'last':
                self.last_n = await self.parse_num(parts[1], element_offset+1)
            elif parts[0] == 'from':
                self.from_date = await self.parse_date(parts[1], element_offset+1)
            elif parts[0] == 'to':
                self.to_date = await self.parse_date(parts[1], element_offset+1)
            else:
                raise CommandFormatException()
            
            parts = parts[2:]
            element_offset += 2
        to_date = self.to_date + 24 * 60 * 60 if self.to_date is not None else None # add 1 day to include the whole day
        result = await self.server_connection.get_user_transactions(self.user_id, from_timestamp=self.from_date, to_timestamp=to_date, \
            last_n=self.last_n)

        transaction_lines = CommandUtils.get_transactions_table(result)
        return transaction_lines if len(result) > 0 else 'No transactions found'

    async def handle_message(self, message: discord.Message) -> bool:
        command_parts = CommandUtils.split_message(message.content)
        formats = f'```{"\n".join("  " + fmt for fmt in TransactionsCommandHandler.FORMATS)}```'
        msg = None
        try: 
            if len(command_parts) >= 4:
                msg = await self.handle_full_command(message, command_parts[len(TransactionsCommandHandler.PREFIX.split()):], \
                    len(TransactionsCommandHandler.PREFIX.split()))
            elif len(command_parts) == 2:
                msg = f'Please use one of the following formats:\n' + formats
            else:
                raise CommandFormatException()
                
        except CommandFormatException as e:
            msg = f'Invalid command format, use:\n' + formats
        except CommandParamException as e:
            # print the original command with '^' under the problematic part
            element_offset = sum(len(part) for part in command_parts[:e.context]) + e.context
            element_len = len(command_parts[e.context])
            msg = f"```{' '.join(command_parts)}\n" + \
                f"{' ' * element_offset}{'^' * element_len}```\n" + \
                f"{str(e)}"
                     
        for msg_part in CommandUtils.slice_message(msg):
            await message.channel.send(msg_part)
        return True
