from collections import namedtuple
from datetime import datetime
import random
from typing import Callable
import discord
from cb_bot.TaskException import TaskFatalException

from cb_bot.common import normalize_message

PingRequestContext = namedtuple('PingRequestContext', ['request_time', 'response_count'])

class LockChannelManager():
    """
    A class that manages the lock channel
    The lock channel is a special channel with only bot access, 
    it is used by a client to query if other clients are currently connected on the same guild, 
    since by design only one chunka_bank client can be connected to a guild at a time
    """

    LOCK_CHANNEL_NAME = 'chunka-bank-lock-channel'
    PING_PHARSE = 'ping'
    PONG_PHARSE = 'pong'
    PING_REQUEST_TIMEOUT_S = 20 # seconds

    async def create_lock_channel(self) -> discord.TextChannel:
        """
        Creates the lock channel
        """
        # create the lock channel
        lock_channel = await self.guild.create_text_channel(LockChannelManager.LOCK_CHANNEL_NAME)
        # set the permissions so that only the bot can access the channel
        await lock_channel.set_permissions(self.guild.default_role, read_messages=False, send_messages=False)
        await lock_channel.set_permissions(self.bot.user, read_messages=True, send_messages=True)
        print(f"Created lock channel: {lock_channel.name} ({lock_channel.id}) in guild '{self.guild.name}' ({self.guild.id}")
        return lock_channel

    async def purge_ping_requests(self):
        """
        Process ping requests on the lock channel
        """
        for request_id in list(self.ping_requests.keys()):
            request_context = self.ping_requests[request_id]
            if request_context.response_count > 0:
                # we got a response, someone else is here
                raise TaskFatalException(f"Another client is already connected to the guild: {self.guild.name} ({self.guild.id})")
            
            if (datetime.now() - request_context.request_time).total_seconds() > LockChannelManager.PING_REQUEST_TIMEOUT_S:
                # remove the request
                del self.ping_requests[request_id]

    def __init__(self, bot: discord.client, register_task: Callable):
        self.bot = bot
        self.ping_requests = {}

        register_task(self.purge_ping_requests)

    async def on_ready(self) -> bool:
        # check which guilds the bot is connected to
        
        if len(self.bot.guilds) > 1:
            guilds_info = '\n'.join([f'  {g.name} ({g.id})' for g in self.bot.guilds])
            raise Exception('More than one guild is not supported, currently connected to:\n' + guilds_info)
        
        # get the guild
        self.guild = self.bot.guilds[0]
        self.lock_channel = next((c for c in self.guild.channels if c.name == LockChannelManager.LOCK_CHANNEL_NAME), None) 
        if self.lock_channel is None: 
            self.lock_channel = await self.create_lock_channel()

        # send ping requets to verify there are no other clients connected
        nonce = str(random.randint(0, 1_000_000_000))
        self.ping_requests[nonce] = PingRequestContext(request_time = datetime.now(), response_count = 0)
        await self.lock_channel.send(f"{LockChannelManager.PING_PHARSE} {nonce}")
        
        return True

    async def on_message(self, message: discord.Message) -> bool:
        """
        Handle a message on the lock channel
        """
        if message.channel != self.lock_channel:
            return False
        
        msg_parts = normalize_message(message.content).split()
        if msg_parts[0] == LockChannelManager.PING_PHARSE:
            if len(msg_parts) < 2:
                await message.channel.send(f"Invalid {LockChannelManager.PING_PHARSE}: Missing request id")
                return True
              
            request_id = msg_parts[1]
            if request_id in self.ping_requests.keys():
                # this is our request, ignore it
                return True
                
            await message.channel.send(f"{LockChannelManager.PONG_PHARSE} {request_id}")
            return True
        elif msg_parts[0] == LockChannelManager.PONG_PHARSE:
            if len(msg_parts) < 2:
                await message.channel.send(f"Invalid {LockChannelManager.PONG_PHARSE}: Missing request id")
                return True
            
            request_id = msg_parts[1]
            if request_id in self.ping_requests.keys():
                count = self.ping_requests[request_id].response_count + 1
                self.ping_requests[request_id] = PingRequestContext(request_time = self.ping_requests[request_id].request_time,
                    response_count = count)
                        
            # this is not our request, ignore it
            return True
                    
        return False


