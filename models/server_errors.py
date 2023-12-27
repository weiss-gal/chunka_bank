from collections import namedtuple
from enum import Enum

class ErrorCodes(Enum):
    OK = 0
    USER_ERROR = 1
    INTERNAL_ERROR = 2

ServerError = namedtuple('ServerError', ['error_code', 'error_msg'])