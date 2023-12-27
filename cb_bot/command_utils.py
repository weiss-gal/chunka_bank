from typing import List

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