from typing import Type
import discord
from cb_bot.cb_server_connection import CBServerConnection
from cb_bot.command_handler import CommandHandler
from cb_bot.common import normalize_message
from cb_bot.interaction_handler import InteractionHandler
from cb_bot.user_info_provider import UserInfoProvider

class UserInteractionManager:
    HELLO_PHRASES = ['hello', 'hi', 'hey', 'sup', 'yo']

    def __init__(self, command_types: list[Type[CommandHandler]], cb_server_connection: CBServerConnection, user_info_provider: UserInfoProvider):
        if any([any([command_type.matches(phrase) for phrase in UserInteractionManager.HELLO_PHRASES]) for command_type in command_types]):
            raise Exception('Command has a conflict with hello phrases')
        
        self.command_types = command_types
        self.server_connection = cb_server_connection
        self.user_info_provider = user_info_provider
        
        # mapping from user id and channel id to interaction handler
        self.users: dict[str, dict[str, InteractionHandler]] = {}

    def get_user_interaction(self, user_id: str, channel_id: str) -> InteractionHandler:
        interactions = self.users.get(user_id, {})
        
        return interactions.get(channel_id)
        
    def set_user_interaction(self, user_id: str, channel_id: str, interaction: InteractionHandler):
        if user_id not in self.users:
            self.users[user_id] = {}
        
        interactions = self.users[user_id]
        if channel_id in interactions:
            raise Exception(f'User {user_id} already has a dialog in channel {channel_id}')

        interactions[channel_id] = interaction

    def unset_user_interaction(self, user_id: str, channel_id: str):
        interaction = self.users[user_id]

        del interaction[channel_id]

    async def handle_message(self, message: discord.Message):
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
    
        interaction = self.get_user_interaction(user_id, channel_id)        
        if interaction is not None:
            res = await interaction.handle_message(message)
            if res: self.unset_user_interaction(user_id, channel_id)

            return
    
        # There is no existing interaction for the user, try to create one
        for command_type in self.command_types:
            if command_type.matches(normalize_message(message.content)):
                command = command_type(user_id, channel_id, self.server_connection, self.user_info_provider)
                self.set_user_interaction(user_id, channel_id, command)
                res = await command.handle_message(message)
                if res: self.unset_user_interaction(user_id, channel_id)
                return
            
        # No known command matches the message
        help_message = 'I can help you with the following commands: \n' + '\n'.join([f"  {command.get_phrase()}" for command in self.command_types])
        if normalize_message(message.content) in UserInteractionManager.HELLO_PHRASES:
            return await message.channel.send('Hello! I am the Chunka Bank bot. ' + help_message)
    
        return await message.channel.send('I do not understand you. ' + help_message)

