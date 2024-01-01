from typing import List

import tabulate

from cb_bot.common import get_user_printable_time
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
        headers = ['Time', 'Amount', 'Description', 'Transaction ID']
        table = [
            [
                get_user_printable_time(t.timestamp),
                t.amount,
                t.description,
                t.id
            ] for t in transactions
        ]

        return '\n'.join([f"`{line}`" for line in tabulate.tabulate(table, headers=headers, tablefmt='orgtbl').split('\n')])

    MAX_DISCORD_MESSAGE_LEN = 2000

    def slice_message(message: str, max_len: int = MAX_DISCORD_MESSAGE_LEN) -> List[str]:
        """Slice a message into multiple messages, each with max_len characters"""
        if len(message) <= max_len:
            return [message]

        result = []
        msg_parts = message.split('\n')
       
        while len(msg_parts) > 0:
            last_index = len(msg_parts) 
            msg_size = 0
            for i in range(len(msg_parts)):
                if msg_size + len(msg_parts[i]) > max_len:
                    last_index = i 
                    break
                msg_size += len(msg_parts[i]) + 1 # +1 for the '\n'

            if last_index == 0:
                raise Exception(f'Cannot slice message: {message}')
            
            print(f'appending {last_index} lines')
            result.append('\n'.join(msg_parts[:last_index]))
            if last_index == len(msg_parts):
                break
            
            msg_parts = msg_parts[last_index:]
            
        print(f'result size is {len(result)}')
        return result