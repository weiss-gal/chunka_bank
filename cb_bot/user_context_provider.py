from cb_bot.dialog import Dialog

class UserContextProvider:

    def __init__(self):
        # mapping from user id and channel id to dialog
        self.users: dict[str, dict[str, Dialog]] = {}

    def get_user_dialog(self, user_id: str, channel_id: str) -> Dialog:
        dialogs = self.users.get(user_id, {})
        
        return dialogs.get(channel_id)
        
    def set_user_dialog(self, user_id: str, channel_id: str, dialog: Dialog):
        if user_id not in self.users:
            self.users[user_id] = {}
        
        dialogs = self.users[user_id]
        if channel_id in dialogs:
            raise Exception(f'User {user_id} already has a dialog in channel {channel_id}')

        dialogs[channel_id] = dialog

    def unset_user_dialog(self, user_id: str, channel_id: str):
        dialogs = self.users[user_id]

        del dialogs[channel_id]

    


