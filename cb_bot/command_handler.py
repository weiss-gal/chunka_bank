import discord

from cb_bot.cb_server_connection import CBServerConnection
from cb_bot.user_manager import UserManager

# Abstract class for a command
class CommandHandler():
    def matches(message: str) -> bool:
        raise NotImplementedError
    
    def get_phrase() -> str:
        raise NotImplementedError

    def __init__(self, user_id, channel_id, server_connection: CBServerConnection, user_manager: UserManager):
        self.user_id = user_id
        self.channel_id = channel_id
        self.server_connection = server_connection
        self.user_manager = user_manager

    # returns true if the command handling is completed
    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError