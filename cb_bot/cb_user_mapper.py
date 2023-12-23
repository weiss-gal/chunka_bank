import csv
from typing import Optional

class UserMapper:
    """A utility class that is used to map discord users to cb users"""
    def __init__(self, mapper_path: str):
        self.mapper_path = mapper_path
        reader = csv.reader(open(mapper_path, 'r'))
        
        next(reader)
        self.discord_2_cb_map = {}
        self.cb_2_discord_map = {}
        for row in reader:
            self.discord_2_cb_map[row[0]] = row[1]
            self.cb_2_discord_map[row[1]] = row[0]

        print("User map: ", self.discord_2_cb_map) # XXX debug

    def get_cb_user_id(self, discord_user_id: str) -> str:
        print(f"getting cb user id for discord user id: [{type(discord_user_id)}] {discord_user_id}") # XXX debug
        print("user map: ", self.discord_2_cb_map) # XXX debug
        result = self.discord_2_cb_map.get(discord_user_id)
        print("result: ", result)
        return result
    
    def get_discord_user_id(self, cb_user_id: str) -> Optional[str]:
        return self.cb_2_discord_map.get(cb_user_id)

