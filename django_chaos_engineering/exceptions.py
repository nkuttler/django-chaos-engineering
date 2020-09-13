class ChaosException(Exception):
    """
    Base chaos exception.
    """


class ChaosExceptionResponse(ChaosException):
    """
    Fallback exception for response actions.
    """


class ChaosExceptionDB(ChaosException):
    """
    Fallback exception for database actions.
    """
