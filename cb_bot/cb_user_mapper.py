from collections import namedtuple
import csv

UserMappingInfo = namedtuple('UserMappingInfo', ['cb_user_id', 'is_admin'])

class UserMapper:
    """A utility class that is used to map discord users to cb users"""
    DEFAULT_INFO = UserMappingInfo(cb_user_id=None, is_admin=False)

    def __init__(self, mapper_path: str):
        self.mapper_path = mapper_path
        reader = csv.reader(open(mapper_path, 'r'))
        
        next(reader)
        self.user_map = {}
        for row in reader:
            cb_user_id = row[1]
            is_admin = row[2].lower() in ['true', 'yes', 'y', '1']
            self.user_map[row[0]] = UserMappingInfo(cb_user_id, is_admin)

    def get_cb_user_id(self, discord_user_id: str) -> str:
        result = self.user_map.get(discord_user_id, UserMapper.DEFAULT_INFO).cb_user_id
        return result
    
    def is_admin(self, discord_user_id: str) -> bool:
        return self.user_map.get(discord_user_id, UserMapper.DEFAULT_INFO).is_admin
    
    def get_user_mapper_info(self, discord_user_id: str) -> UserMappingInfo:
        return self.user_map.get(discord_user_id, UserMapper.DEFAULT_INFO)

