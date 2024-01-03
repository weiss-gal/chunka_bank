from datetime import datetime

from cb_bot.user_info_provider import ExternalUserInfo

def normalize_message(message):
    return message.strip().lower()

def get_user_printable_time(timestamp: int):
    return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')

def get_printable_user_name(user_info: ExternalUserInfo, is_discord_format: bool = True):
    if is_discord_format:
        return f'**{user_info.display_name} ({user_info.name})**'
    
    return f"'{user_info.display_name}'"