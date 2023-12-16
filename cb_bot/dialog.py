import discord
from cb_bot.cb_server_connection import CBServerConnection
from cb_bot.command_handler import CommandHandler
from cb_bot.common import normalize_message

class Dialog:
    """Class for a session"""
    HELLO_PHRASES = ['hello', 'hi', 'hey', 'sup']

    def __init__(self, user_id, channel_id, command_types: list[CommandHandler], cb_server_connection: CBServerConnection):
        self.user_id = user_id
        self.channel_id = channel_id
        self.command_types = command_types
        self.server_connection = cb_server_connection
        self.active_command = None
    
    async def handle_message(self, message: discord.Message):
        if self.active_command:
            res = await self.active_command.handle_message(message)
            if res: self.active_command = None

            return

        for command in self.command_types:
            if command.matches(normalize_message(message.content)):
                self.active_command = command(self.user_id, self.channel_id, self.server_connection)
                await self.active_command.handle_message(message)
                
                return

        help_message = 'I can help you with the following commands: \n' + '\n'.join([f"  {command.get_phrase()}" for command in self.command_types])
        if normalize_message(message.content) in Dialog.HELLO_PHRASES:
            return await message.channel.send('Hello! I am the Chunka Bank bot. ' + help_message)
        
        return await message.channel.send('I do not understand you. ' + help_message)
        