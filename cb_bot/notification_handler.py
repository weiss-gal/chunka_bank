import discord
from cb_bot.request_handler import RequestHandler

class NotificationHandler(RequestHandler):
    def __init__(self, user_id: str, message: str):
        super().__init__(user_id)
        self.message = message

    async def initiate_interaction(self, channel: discord.channel) -> bool:
        print(f"sending notification to user id {self.user_id}:  {self.message}")
        await channel.send(self.message)
        return True

    async def handle_message(self, message: discord.Message) -> bool:
        raise Exception('NotificationHandler should not receive messages')
