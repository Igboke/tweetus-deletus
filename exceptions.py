class LoaderError(Exception):
    pass

class FileReadError(LoaderError):
    pass

class DataParseError(LoaderError):
    pass

class RateLimitException(Exception):
    pass

class ServiceUnavailableException(Exception):
    pass