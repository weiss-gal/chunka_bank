import discord
from .command_handler import CommandHandler

class TransferCommandHandler(CommandHandler):
    PHRASE = 'transfer'

    def matches(message: str) -> bool:
        return message.split(' ')[0] == TransferCommandHandler.PHRASE
    
    def get_phrase() -> str:
        return TransferCommandHandler.PHRASE

    async def handle_message(self, message: discord.Message) -> bool:
        ### TODO: implement this
        #balance = await self.server_connection.get_user_balance(self.user_id)
        #await message.channel.send(f'Your balance is {balance}')
        await message.channel.send(f'Not implemented yet')
        return True