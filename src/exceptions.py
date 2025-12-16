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

class DatabaseError(Exception):
    pass

class DatabaseConnectionError(DatabaseError):
    pass

class DatabaseReadError(DatabaseError):
    pass

class DatabaseWriteError(DatabaseError):
    pass