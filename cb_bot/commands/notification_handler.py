import discord
from cb_bot.command_utils import CommandUtils
from cb_bot.request_handler import RequestHandler

class NotificationHandler(RequestHandler):
    def __init__(self, user_id: str, message: str):
        super().__init__(user_id)
        self.message = message

    async def initiate_interaction(self, channel: discord.channel) -> bool:
        print(f"sending notification to user id {self.user_id}:  {self.message}")
        for msg_part in CommandUtils.slice_message(self.message):
            await channel.send(msg_part)

        return True

    async def handle_message(self, message: discord.Message) -> bool:
        raise Exception('NotificationHandler should not receive messages')
