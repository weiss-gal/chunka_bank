from collections import namedtuple
import discord
import sys

Config = namedtuple('Config', ['bot_token'])

def parse_args(args):
    if len(args) != 2:
        print(f'Usage: {args[0]} <bot_token>')
        sys.exit(1)

    return Config(args[1])

def main(args):

    config = parse_args(args)
    bot_token = config.bot_token
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)
    @client.event
    async def on_ready():
        print(f"Bot {client.user} is ready")

    @client.event
    async def on_message(message):
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