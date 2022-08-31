class NotForSendingError(Exception):
    """Error class for errors that we won't send to TG."""

    pass


class MissingCostantError(NotForSendingError):
    """Any of the vital constants not found."""

    pass


class NotExpectedHwStatusError(Exception):
    """API answer contains unknown Hw status."""

    pass


class NotOkResponseError(Exception):
    """Request got not OK Status."""

    pass
