'''
Abstract class for a Request
Request is a special type of interaction that is not initiated by the user, but rather by the bot itself
It may be a one time notification, or a request for a response from the user
'''
import discord
from cb_bot.interaction_handler import InteractionHandler

class RequestHandler(InteractionHandler):
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def get_userid(self):
        return self.user_id

    # returns true if the command handling is completed
    async def initiate_interaction(self, channel: discord.channel) -> bool:
        raise NotImplementedError

    async def handle_message(self, message: discord.Message) -> bool:
        raise NotImplementedError
