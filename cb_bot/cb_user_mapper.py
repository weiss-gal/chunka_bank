import csv

class UserMapper:
    """A utility class that is used to map discord users to cb users"""
    def __init__(self, mapper_path: str):
        self.mapper_path = mapper_path
        reader = csv.reader(open(mapper_path, 'r'))
        
        next(reader)
        self.user_map = {}
        for row in reader:
            self.user_map[row[0]] = row[1]

    def get_cb_user_id(self, discord_user_id: str) -> str:
        return self.user_map.get(discord_user_id)
