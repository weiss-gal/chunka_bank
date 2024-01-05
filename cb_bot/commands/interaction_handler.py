import discord

class InteractionHandler():
    TIMEOUT_S = 60*2 # 2 minutes timeout is the default

    def __init__(self):
        raise NotImplementedError
    
    # returns true if the command handling is completed
    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError
    
    async def check_expired(self) -> bool:
        raise NotImplementedError
