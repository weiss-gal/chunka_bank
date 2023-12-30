from collections import namedtuple

# time is saved as linux timestamp
UserTransactionInfo = namedtuple('UserTransactionInfo', ['userid', 'amount', 'timestamp', 'description', 'id'])
