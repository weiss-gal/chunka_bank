from typing import Type
import discord
from cb_bot.cb_server_connection import CBServerConnection
from cb_bot.cb_user_mapper import UserMapper
from cb_bot.commands.command_handler import CommandHandler
from cb_bot.common import normalize_message
from cb_bot.commands.interaction_handler import InteractionHandler
from cb_bot.commands.request_handler import RequestHandler
from cb_bot.user_info_provider import UserInfoProvider

class UserChannelState:
    def __init__(self, interaction_handler: InteractionHandler = None, queue: list[RequestHandler] = []):
        self.interaction_handler = interaction_handler
        self.queue = queue

class UserChannelStateProvider:
    def __init__(self):
        self.users: dict[str, dict[str, UserChannelState]] = {}

    def get_interaction(self, user_id: str, channel_id: str) -> InteractionHandler:
        if user_id not in self.users or channel_id not in self.users[user_id]:
            return None
        
        return self.users[user_id][channel_id].interaction_handler

    def set_interaction(self, user_id: str, channel_id: str, interaction: InteractionHandler):
        if user_id not in self.users:
            self.users[user_id] = {}
        if channel_id not in self.users[user_id]:
            self.users[user_id][channel_id] = UserChannelState(None, [])
        if self.users[user_id][channel_id].interaction_handler is not None:
            raise Exception(f'User {user_id} already has an active handler for channel {channel_id}')
        
        self.users[user_id][channel_id].interaction_handler = interaction

    def unset_interaction(self, user_id: str, channel_id: str):
        if self.users[user_id][channel_id].interaction_handler is None:
            raise Exception(f'User {user_id} does not have an active handler for channel {channel_id}')
            
        self.users[user_id][channel_id].interaction_handler = None

    def queue_request(self, user_id: str, channel_id: str, request: RequestHandler):
        if user_id not in self.users:
            self.users[user_id] = {}
        if channel_id not in self.users[user_id]:
            self.users[user_id][channel_id] = UserChannelState(None, [])
        
        self.users[user_id][channel_id].queue.append(request)

    def try_dequeue_request(self, user_id: str, channel_id: str) -> RequestHandler:
        q = self.users[user_id][channel_id].queue
        return q.pop(0) if len(q) > 0 else None
    
    def get_all_users(self) -> list[str]:
        return list(self.users.keys())
    
    def get_all_channels(self, user_id: str) -> list[str]:
        return list(self.users.get(user_id, {}).keys())

class UserInteractionManager:
    HELLO_PHRASES = ['hello', 'hi', 'hey', 'sup', 'yo']

    async def process_queued_interactions(self):
        for user_id in self.user_interaction_provider.get_all_users():
            for channel_id in self.user_interaction_provider.get_all_channels(user_id):
                if self.user_interaction_provider.get_interaction(user_id, channel_id) is not None:
                    continue
                
                request = self.user_interaction_provider.try_dequeue_request(user_id, channel_id)
                if request is None:
                    continue
                
                self.user_interaction_provider.set_interaction(user_id, channel_id, request)
                res = await request.initiate_interaction(self.user_info_provider.get_user_info(user_id).dm_channel)
                if res: self.user_interaction_provider.unset_interaction(user_id, channel_id)

    def __init__(self, command_types: list[Type[CommandHandler]], cb_server_connection: CBServerConnection, 
                 user_info_provider: UserInfoProvider, user_mapper: UserMapper, register_fast_task: callable):
        
        if any([any([command_type.matches(phrase) for phrase in UserInteractionManager.HELLO_PHRASES]) for command_type in command_types]):
            raise Exception('Command has a conflict with hello phrases')
        
        self.command_types = command_types
        self.server_connection = cb_server_connection
        self.user_info_provider = user_info_provider
        self.user_mapper = user_mapper
        self.user_interaction_provider = UserChannelStateProvider()
        
        # mapping from user id and channel id to interaction handler
        self.users: dict[str, dict[str, UserChannelState]] = {}

        register_fast_task(self.process_queued_interactions)

    def get_user_command_types(self, user_id: str) -> list[Type[CommandHandler]]:
        return [command_type for command_type in self.command_types if command_type.is_allowed(self.user_mapper.get_user_mapper_info(user_id))]

    async def handle_message(self, message: discord.Message):
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
    
        interaction = self.user_interaction_provider.get_interaction(user_id, channel_id)        
        if interaction is not None:
            res = await interaction.handle_message(message)
            if res: self.user_interaction_provider.unset_interaction(user_id, channel_id)

            return
    
        # There is no existing interaction for the user, try to create one
        for command_type in self.get_user_command_types(user_id):
            if command_type.matches(normalize_message(message.content)):
                # instantiate the command handler
                command = command_type(user_id, channel_id, self.server_connection, self.user_info_provider, self.queue_interaction)
                self.user_interaction_provider.set_interaction(user_id, channel_id, command)
                res = await command.handle_message(message)
                if res: self.user_interaction_provider.unset_interaction(user_id, channel_id)
                return
            
        # No known command matches the message
        commands = [command.get_prefix() for command in self.get_user_command_types(user_id)]
        commands.sort()
        help_message = 'I can help you with the following commands: \n' + '\n'.join([f"  **{command}**" for command in commands])
        if normalize_message(message.content) in UserInteractionManager.HELLO_PHRASES:
            return await message.channel.send('Hello! I am the Chunka Bank bot. ' + help_message)
    
        return await message.channel.send('I do not understand you. ' + help_message)

    def queue_interaction(self, user_id: str, interaction: InteractionHandler):
        user_info = self.user_info_provider.get_user_info(user_id)
        self.user_interaction_provider.queue_request(user_id, str(user_info.dm_channel.id), interaction)
