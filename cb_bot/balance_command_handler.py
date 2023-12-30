import discord
from .command_handler import CommandHandler

class BalanceCommandHandler(CommandHandler):
    PREFIX = 'show balance'

    def matches(message: str) -> bool:
        return message.startswith(BalanceCommandHandler.PREFIX)
    
    def get_prefix() -> str:
        return BalanceCommandHandler.PREFIX

    async def handle_message(self, message: discord.Message) -> bool:
        balance = await self.server_connection.get_user_balance(self.user_id)
        await message.channel.send(f'Your balance is **{balance}**')
        return True