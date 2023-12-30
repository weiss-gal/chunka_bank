from datetime import datetime

def normalize_message(message):
    return message.strip().lower()

def get_user_printable_time(timestamp: int):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')