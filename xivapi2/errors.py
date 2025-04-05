class XivApiError(Exception):
    """
    Base exception class for all XIVAPI errors.
    """

    ...


class XivApiNotFoundError(XivApiError):
    """
    Exception raised when a requested resource (sheet, row, etc.) is not found.
    """

    ...


class XivApiParameterError(XivApiError):
    """
    Exception raised when an invalid parameter is provided to the API.
    """

    ...


class XivApiRateLimitError(XivApiError):
    """
    Exception raised when the API rate limit is exceeded.
    """

    ...


class XivApiServerError(XivApiError):
    """
    Exception raised when the XIVAPI server returns an internal server error.
    """

    ...
