import discord

from cb_bot.commands.command_utils import CommandUtils
from .command_handler import CommandHandler

class ShowUsersCommandHandler(CommandHandler):
    PREFIX = 'show users'

    def matches(message: str) -> bool:
        return message.startswith(ShowUsersCommandHandler.PREFIX)
    
    def get_prefix() -> str:
        return ShowUsersCommandHandler.PREFIX

    async def handle_message(self, message: discord.Message) -> bool:
        msg = 'Users:\n' + CommandUtils.get_users_table(self.user_info_provider.get_all_users())
        await message.channel.send(msg)
        return True
    
    async def check_expired(self) -> bool:
        return False # never expires