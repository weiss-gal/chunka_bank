import discord

from cb_bot.commands.command_utils import CommandUtils
from .command_handler import CommandHandler

class BalanceCommandHandler(CommandHandler):
    """
    Handle the show balance command
    The following formats are supported:
    - show balance
    - show balance for <user>
    """

    PREFIX = 'show balance'
    FORMAT = f'{PREFIX} [for <user>]'

    def matches(message: str) -> bool:
        return message.startswith(BalanceCommandHandler.PREFIX)
    
    def get_prefix() -> str:
        return BalanceCommandHandler.PREFIX
    
    async def handle_show_balance(self, user_id: str, channel: discord.channel) -> bool:
        balance = await self.server_connection.get_user_balance(self.user_id)
        user_phrase = "your" if user_id == self.user_id else f"{self.user_info_provider.get_user_info(user_id).display_name}'s"

        await channel.send(f'{user_phrase} balance is **{balance}**')
        return True

    async def handle_message(self, message: discord.Message) -> bool:
        command_parts = CommandUtils.split_message(message.content)
        user_id = self.user_id
        if len(command_parts) > 2:
            if command_parts[2] != 'for' or len(command_parts) < 4:
                await message.channel.send(f'Invalid command, please use the following format:\n{BalanceCommandHandler.FORMAT}')
                return True
            
            search_str = " ".join(command_parts[3:])
            users = self.user_info_provider.search_user(search_str)
            if len(users) == 0:
                await message.channel.send(f"The name '{search_str}' does not match any know user")
                return True
            
            if len(users) > 1:
                await message.channel.send(f"The name '{search_str}' matches multiple users, please specify the user by typing their name or alias:\n" + \
                    CommandUtils.get_users_table(users))
                return True
            
            user_id = users[0].user_id
            if user_id != self.user_id and not self.is_admin:
                await message.channel.send(f'You are not allowed to see the balance for other users')
                return True
                

        return await self.handle_show_balance(user_id, message.channel)
    
    async def check_expired(self) -> bool:
        return False # never expires