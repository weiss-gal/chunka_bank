import discord
from .command_handler import CommandHandler

class BalanceCommandHandler(CommandHandler):
    PHRASE = 'balance'

    def matches(message: str) -> bool:
        return message.split(' ')[0] == BalanceCommandHandler.PHRASE
    
    def get_phrase() -> str:
        return BalanceCommandHandler.PHRASE

    async def handle_message(self, message: discord.Message) -> bool:
        balance = await self.server_connection.get_user_balance(self.user_id)
        await message.channel.send(f'Your balance is **{balance}**')
        return True