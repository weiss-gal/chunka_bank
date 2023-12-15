import discord

# Abstract class for a command
class CommandHandler():
    def matches(message: str) -> bool:
        raise NotImplementedError
    
    def get_phrase() -> str:
        raise NotImplementedError

    def __init__(self, user_id, channel_id):
        self.user_id = user_id
        self.channel_id = channel_id

    # returns true if the command handling is completed
    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError