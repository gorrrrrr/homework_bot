class MissingCostantException(Exception):
    """Any of the vital constants not found."""

    pass


class NotExpectedHwStatusException(Exception):
    """API answer contains unknown Hw status."""

    pass
