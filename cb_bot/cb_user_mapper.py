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

        print("User map: ", self.user_map) # XXX debug

    def get_cb_user_id(self, discord_user_id: str) -> str:
        print(f"getting cb user id for discord user id: [{type(discord_user_id)}] {discord_user_id}") # XXX debug
        print("user map: ", self.user_map) # XXX debug
        result = self.user_map.get(discord_user_id)
        print("result: ", result)
        return result
