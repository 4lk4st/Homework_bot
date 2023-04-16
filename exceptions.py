class APIResponseError(Exception):
    pass

class NoStatusError(KeyError):
    pass

class BadStatusError(KeyError):
    pass

class NoHwNameError(KeyError):
    pass