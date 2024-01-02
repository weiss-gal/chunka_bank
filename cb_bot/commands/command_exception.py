class CommandFormatException(Exception):
    pass

class CommandParamException(Exception):
    def __init__(self, msg: str, context=None):
        super().__init__(msg)
        self.context = context # any object that can be used to provide context for the error
    pass