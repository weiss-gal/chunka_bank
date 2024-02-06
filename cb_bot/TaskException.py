class TaskException(Exception):
    """
    Exception that indicates that a task has failed
    """
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message

class TaskFatalException(TaskException):
    """
    Exception that indicates that a task has failed so fatally that the bot should stop
    """
