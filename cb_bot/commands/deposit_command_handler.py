from cb_bot.cb_user_mapper import UserMappingInfo
from cb_bot.commands.command_utils import CommandUtils
from cb_bot.commands.transfer_command_handler import TransferCommandHandler

class DepositCommandHandler(TransferCommandHandler):
    """
    Handle the deposit command
    The following formats are supported:
    - deposit 
    - deposit <amount> to <username> [description]
    """
    PHRASE = 'deposit'
    FORMAT = f'{PHRASE} <amount> to <username> [description]'

    def is_allowed(user_mapping_info: UserMappingInfo) -> bool:
        return user_mapping_info.is_admin

    def matches(message: str) -> bool:
        return CommandUtils.split_message(message)[0] == DepositCommandHandler.PHRASE
    
    def get_prefix() -> str:
        return DepositCommandHandler.PHRASE
    
    def get_default_description(self) -> str:
        return f"Deposit {self.amount} to '{self.user_info_provider.get_user_info(self.to).display_name}' account"
    