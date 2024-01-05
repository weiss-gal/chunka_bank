import discord
from cb_bot.commands.command_utils import CommandUtils
from cb_bot.commands.request_handler import RequestHandler

class NotificationHandler(RequestHandler):
    def __init__(self, user_id: str, message: str):
        super().__init__(user_id)
        self.message = message

    async def initiate_interaction(self, channel: discord.channel) -> bool:
        print(f"sending notification to user id {self.user_id}:  {self.message}")
        ltr_prefix = '`...more...`'
        for msg_part in CommandUtils.slice_message(self.message, prefix=ltr_prefix):
            await channel.send(msg_part)

        return True

    async def handle_message(self, message: discord.Message) -> bool:
        raise Exception('NotificationHandler should not receive messages')
    
    async def check_expired(self) -> bool:
        return False # never expires

