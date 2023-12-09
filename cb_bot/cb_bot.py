from collections import namedtuple
import discord
import sys

Config = namedtuple('Config', ['bot_token', 'cb_server_url'])

def get_env_config():
    import os
    return Config(
        bot_token=os.environ['BOT_TOKEN'],
        cb_server_url=os.environ.get('CB_SERVER_URL')
    )

def parse_args(args):
    if len(args) > 2:
        print(f'Usage: {args[0]} [bot_token>]')
        sys.exit(1)

    return Config(bot_token=None if len(args) == 1 else args[1], cb_server_url=None)

def main(args):

    env_config = get_env_config()
    cmdline_config = parse_args(args)
    merge_config = {**env_config._asdict(), **cmdline_config._asdict()}
    config = Config(**merge_config)

    bot_token = config.bot_token
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

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

        # if the user is the client user itself, ignore the message
        if user == client.user:
            return


        if message.content == "ping":
            await message.channel.send("pong")
        elif message.content == "pong":
            await message.channel.send("ping")
        elif message.content == "bal":
            await message.channel.send("You have 0 coins")
        elif message.content == "help":
            await message.channel.send("Commands: bal, ping, pong, help")

    client.run(bot_token)

if __name__ == '__main__':
    main(sys.argv)