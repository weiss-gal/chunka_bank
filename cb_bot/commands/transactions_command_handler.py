from datetime import datetime
from typing import Callable, List
import discord
from cb_bot.cb_server_connection import CBServerConnection
from cb_bot.commands.command_exception import CommandFormatException, CommandParamException

from cb_bot.commands.command_utils import CommandUtils
from cb_bot.user_info_provider import UserInfoProvider
from .command_handler import CommandHandler

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    async def handle_full_command(self, message: discord.Message, command_parts: List[str], element_offset) -> bool:
        parts = [p for p in command_parts] # deep copy
        while len(parts) > 0:
            if len(parts) < 2:
                raise CommandFormatException()
            
            if parts[0] == 'last':
                self.last_n = CommandUtils.parse_amount(parts[1], element_offset+1)
            elif parts[0] == 'from':
                self.from_date = self.parse_date(parts[1], element_offset+1)
            elif parts[0] == 'to':
                self.to_date = self.parse_date(parts[1], element_offset+1)
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
            msg = CommandUtils.get_param_error_msg(e, command_parts)
                     
        for msg_part in CommandUtils.slice_message(msg):
            await message.channel.send(msg_part)
        return True
