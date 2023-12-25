from typing import List

class CommandUtils:
    """Break down a message into a command and its arguments"""
    def split_message(message: str) -> List[str]:
        split_message = message.split()
        return split_message