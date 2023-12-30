import discord

class InteractionHandler():
    def __init__(self):
        raise NotImplementedError
    
    # returns true if the command handling is completed
    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError
