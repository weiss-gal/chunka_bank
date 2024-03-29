from typing import Callable, List

from cb_bot.commands.command_exception import CommandParamException

from cb_bot.common import get_printable_user_name, get_user_printable_time
from cb_bot.user_info_provider import ExternalUserInfo
from models.transactions import UserTransactionInfo

class CommandUtils:
    """Break down a message into a command and its arguments"""
    def split_message(message: str) -> List[str]:
        split_message = message.split()
        return split_message
    
    def highlight(message: str, before: bool) -> str:
        '''Highlight a message with with headiing or trailing marker line'''
        marker_sign = '='
        if before:
            first_line_len = len(message.split('\n')[0])
            return f'{marker_sign * first_line_len}\n{message}'
    
        last_line_len = len(message.split('\n')[-1])
        return f'{message}\n{marker_sign * last_line_len}'

    def get_transactions_table(transactions: List[UserTransactionInfo]) -> str:
        response = ''
        for t in transactions:
            aligned_amount = f'{t.amount:.2f}'.rjust(10)
            response += f'**`{t.description}`**\n' + \
                f'`{aligned_amount} | {get_user_printable_time(t.timestamp)}`\n\n'
        return response

    MAX_DISCORD_MESSAGE_LEN = 2000

    def slice_message(message: str, prefix: str = None, max_len: int = MAX_DISCORD_MESSAGE_LEN) -> List[str]:
        """Slice a message into multiple messages, each with max_len characters"""
        if len(message) <= max_len:
            return [message]

        result = []
        msg_lines = message.split('\n')
        is_first = True
        while len(msg_lines) > 0:
            last_index = len(msg_lines) 
            msg_size = 0 if prefix is None and not is_first else len(prefix) + 1 # +1 for the '\n'
            for i in range(len(msg_lines)):
                if msg_size + len(msg_lines[i]) > max_len:
                    last_index = i 
                    break
                msg_size += len(msg_lines[i]) + 1 # +1 for the '\n'

            if last_index == 0:
                raise Exception(f'Cannot slice message: {message}')
            
            print(f'appending {last_index} lines')

            msg_part = msg_lines[:last_index]
            if not is_first and prefix is not None:
                msg_part.insert(0, prefix)

            result.append('\n'.join(msg_part))
            if last_index == len(msg_lines):
                break
            
            msg_lines = msg_lines[last_index:]
            is_first = False
            
        print(f'result size is {len(result)}')
        return result
    
    async def handle_confirmation(command_parts: List[str], cancelled: Callable, confirmed: Callable) -> str:
        FORMAT = "please confirm by typing *yes* or cancel by typing *no*"
        if len(command_parts) != 1 or command_parts[0].lower() not in ['yes', 'y', 'no', 'n']:
            return f"I did not understand, {FORMAT}"

        if command_parts[0].lower() in ['no', 'n']:
            return await cancelled()
        return await confirmed()
    
    def get_param_error_msg(e: CommandParamException, command_parts: List[str]) -> str:
         # print the original command with '^' under the problematic part
        element_offset = sum(len(part) for part in command_parts[:e.context]) + e.context
        element_len = len(command_parts[e.context])
        return f"```{' '.join(command_parts)}\n" + \
            f"{' ' * element_offset}{'^' * element_len}```\n" + \
            f"{str(e)}"
        
    def parse_amount(num_str: str, context) -> float:
        try:
            num = float(num_str)
            if num <= 0:
                raise CommandParamException('must be positive', context)
            return num
        except ValueError:
            raise CommandParamException('invalid number', context)
        
    def parse_n(num_str: str, context) -> int:
        """Parse a positive integer"""
        try:
            num = int(num_str)
            if num <= 0:
                raise CommandParamException('must be positive', context)
            return num
        except ValueError:
            raise CommandParamException('invalid number', context)

    def get_expired_msg() -> str:
        return '**Sorry**, I think you forgot about me, please start over'
    
    def get_users_table(users: List[ExternalUserInfo]) -> str:
        return "\n".join(["  " + get_printable_user_name(user) for user in users])
        