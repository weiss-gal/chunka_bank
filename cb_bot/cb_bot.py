from collections import namedtuple
import logging
import signal
import discord
from discord.ext import tasks
from discord.ext import commands
import sys

from cb_bot.cb_server_connection import CBServerConnection
from cb_bot.cb_user_mapper import UserMapper
from .transfer_command_handler import TransferCommandHandler
from .balance_command_handler import BalanceCommandHandler
from .dialog import Dialog

Config = namedtuple('Config', ['bot_token', 'cb_server_url', 'mapper_path', 'is_debug'])

def get_env_config():
    import os

    return {
        'bot_token': os.environ.get('BOT_TOKEN'),
        'cb_server_url': os.environ.get('CB_SERVER_URL'),
        'mapper_path': os.environ.get('MAPPER_PATH')
    }

def parse_args(args):
    if len(args) > 2:
        print(f'Usage: {args[0]} [bot_token>]')
        sys.exit(1)

    return {
        'bot_token': args[1] if len(args) == 2 else None
    }

def get_dialog_key(user_id, channel_id):
    return f'{user_id}-{channel_id}'

def get_dialog(user_id, channel_id, dialogs):
    key = get_dialog_key(user_id, channel_id)
    return dialogs.get(key)

def add_dialog(user_id, channel_id, dialog, dialogs):
    key = get_dialog_key(user_id, channel_id)
    dialogs[key] = dialog

def main(args):
    default_config = Config(bot_token=None, cb_server_url='http://localhost:5000', mapper_path=None, is_debug=True)
    env_config = get_env_config()
    cmdline_config = parse_args(args)
    
    merge_config = {}
    for c in [default_config._asdict(), env_config, cmdline_config]:
        merge_config = {**merge_config, **{key: value for (key, value) in c.items() if value is not None}}

    config = Config(**merge_config)

    if config.bot_token is None:
        print('Error: BOT_TOKEN is not set, use environment variable or command line argument')
        sys.exit(1)

    bot_token = config.bot_token
    
    logging.basicConfig(filename='cb_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    command_types = [
        BalanceCommandHandler,
        TransferCommandHandler
    ]

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    user_mapper = UserMapper(config.mapper_path)
    cb_server_connection = CBServerConnection(config.cb_server_url, user_mapper)

    client = commands.Bot(command_prefix='', intents=intents)
    dialogs = {}
    fast_tasks = [] # every second

    # this is the channel used to send notifications to all users
    general_channel = None

    # tasks to be executed every second
    @tasks.loop(seconds=1)  
    async def execute_fast_tasks():
        for task in fast_tasks:
            await task()

    # tasks to be executed every 10 seconds

    @tasks.loop(seconds=10)
    async def execute_slow_tasks():
        if len(client.guilds) > 1:
            raise Exception('More than one guild is not supported')

    @client.event
    async def on_ready():
        nonlocal general_channel
        print(f"Bot {client.user} is ready")
        execute_fast_tasks.start()
        execute_slow_tasks.start()
        # print message on general channel
        general_channel = [channel for channel in client.get_all_channels() if channel.name == 'general'][0]
        await general_channel.send(f"Bot _{client.user}_ is ready\n" + 
                                   "To ") # XXX complete this message

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
        
        user_id = str(user.id)
        channel_id = str(channel.id)

        try:        
            # if there is an existing dialog for the user, use it
            dialog = get_dialog(str(user.id), channel.id, dialogs)
            if dialog:
                await dialog.handle_message(message)
                return
                    
            dialog = Dialog(user_id, channel_id, command_types, cb_server_connection)
            add_dialog(user_id, channel_id, dialog, dialogs)
            await dialog.handle_message(message)
        except Exception as e:
            logging.exception(e)
            if config.is_debug:
                await message.channel.send(f'Error: {e}')
            else:
                await message.channel.send('Error: Handling message failed')

            dialogs.pop(get_dialog_key(user_id, channel_id))

    is_stopped = False # used to stop the bot forcefully when SIGINT(ctrl-c) is received twice
    def terminanation_handler(sig, frame):
        nonlocal is_stopped
        if is_stopped:
            exit(0)
        
        is_stopped = True
        print(f"Bot {client.user} is going to sleep")
        async def stop():
            if general_channel is not None:
                await general_channel.send(f"Bot _{client.user}_ is going to sleep\n" + 
                                            "Bye bye. ")
            await client.close()
        
        fast_tasks.append(stop)
        
    signal.signal(signal.SIGINT, terminanation_handler)

    client.run(bot_token)

if __name__ == '__main__':
    main(sys.argv)