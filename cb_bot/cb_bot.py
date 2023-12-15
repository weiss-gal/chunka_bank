from collections import namedtuple
import logging
import discord
from discord.ext import commands
import sys
from cb_bot.common import normalize_message

Config = namedtuple('Config', ['bot_token', 'cb_server_url'])

# Abstract class for a command
class CommandHandler():
    def matches(message: str) -> bool:
        raise NotImplementedError
    
    def get_phrase() -> str:
        raise NotImplementedError

    def __init__(self, user_id, channel_id):
        self.user_id = user_id
        self.channel_id = channel_id

    # returns true if the command handling is completed
    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError

class BalanceCommandHandler(CommandHandler):
    PHRASE = 'balance'

    def matches(message: str) -> bool:
        return message.split(' ')[0] == BalanceCommandHandler.PHRASE
    
    def get_phrase() -> str:
        return BalanceCommandHandler.PHRASE

    async def handle_message(self, message: discord.Message) -> bool:
        await message.channel.send('Your balance is 1000')
        return True

# Abstract class for a session
class Dialog:
    HELLO_PHRASES = ['hello', 'hi', 'hey', 'sup']

    def __init__(self, user_id, channel_id, command_types: list[CommandHandler]):
        self.user_id = user_id
        self.channel_id = channel_id
        self.command_types = command_types
        self.active_command = None
    
    async def handle_message(self, message):
        if self.active_command:
            res = await self.active_command.handle_message(message)
            if res: self.active_command = None

            return

        for command in self.command_types:
            if command.matches(normalize_message(message.content)):
                self.active_command = command(self.user_id, self.channel_id)
                await self.active_command.handle_message(message)
                
                return

        help_message = 'I can help you with the following commands: \n' + '\n'.join([f"  {command.get_phrase()}" for command in self.command_types])
        if normalize_message(message.content) in Dialog.HELLO_PHRASES:
            return await message.channel.send('Hello! I am the Chunka Bank bot. ' + help_message)
        
        return await message.channel.send('I do not understand you. ' + help_message)
        
def get_env_config():
    import os

    return Config(
        bot_token=os.environ.get('BOT_TOKEN'),
        cb_server_url=os.environ.get('CB_SERVER_URL')
    )

def parse_args(args):
    if len(args) > 2:
        print(f'Usage: {args[0]} [bot_token>]')
        sys.exit(1)

    return Config(bot_token=None if len(args) == 1 else args[1], cb_server_url=None)

def get_dialog_key(user_id, channel_id):
    return f'{user_id}-{channel_id}'

def get_dialog(user_id, channel_id, dialogs):
    key = get_dialog_key(user_id, channel_id)
    return dialogs.get(key)

def add_dialog(user_id, channel_id, dialog, dialogs):
    key = get_dialog_key(user_id, channel_id)
    dialogs[key] = dialog

def main(args):
    env_config = get_env_config()
    cmdline_config = parse_args(args)
    
    merge_config = {**env_config._asdict(), **{key: value for (key, value) in cmdline_config._asdict().items() if value is not None}}
    config = Config(**merge_config)

    if config.bot_token is None:
        print('Error: BOT_TOKEN is not set, use environment variable or command line argument')
        sys.exit(1)

    bot_token = config.bot_token
    
    logging.basicConfig(filename='cb_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    command_types = [BalanceCommandHandler]

    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)
    dialogs = {}

    @client.event
    async def on_ready():
        print(f"Bot {client.user} is ready")

    @client.event
    async def on_message(message):
        # this is the string text message of the Message
        content = message.content
        # this is the sender of the Message
        user = message.author
        # this is the channel of there the message is sent
        channel = message.channel
        logging.info(f"Message recieved: {content}, User: {user}, Channel: {channel}")
        # if the user is the client user itself, ignore the message
        if user == client.user:
            return

        # if there is an existing dialog for the user, use it
        dialog = get_dialog(user.id, channel.id, dialogs)
        if dialog:
            await dialog.handle_message(message)
            return
        
        dialog = Dialog(user.id, channel.id, command_types)
        add_dialog(user.id, channel.id, dialog, dialogs)
        await dialog.handle_message(message)

    client.run(bot_token)

if __name__ == '__main__':
    main(sys.argv)