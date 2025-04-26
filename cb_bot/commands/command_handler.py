from typing import Callable
import discord

from cb_bot.cb_server_connection import CBServerConnection
from cb_bot.cb_user_mapper import UserMappingInfo
from cb_bot.commands.interaction_handler import InteractionHandler
from cb_bot.user_info_provider import UserInfoProvider

# Abstract class for a command
class CommandHandler(InteractionHandler):
    def matches(message: str) -> bool:
        raise NotImplementedError
    
    def get_prefix() -> str:
        raise NotImplementedError
    
    def get_brief() -> str:
        raise NotImplementedError
    
    def is_allowed(user_mapping_info: UserMappingInfo) -> bool:
        # by default, all commands are allowed
        return True

    def __init__(self, user_id, channel_id, server_connection: CBServerConnection, user_info_provider: UserInfoProvider,
            is_admin: bool, queue_interaction: Callable):
        self.user_id = user_id
        self.channel_id = channel_id
        self.server_connection = server_connection
        self.user_info_provider = user_info_provider
        self.queue_interaction = queue_interaction
        self.is_admin: bool = is_admin

    # returns true if the command handling is completed
    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError