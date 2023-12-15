import discord
from .command_handler import CommandHandler

class BalanceCommandHandler(CommandHandler):
    PHRASE = 'balance'

    def matches(message: str) -> bool:
        return message.split(' ')[0] == BalanceCommandHandler.PHRASE
    
    def get_phrase() -> str:
        return BalanceCommandHandler.PHRASE

    async def handle_message(self, message: discord.Message) -> bool:
        await message.channel.send('Your balance is 1000')
        return True