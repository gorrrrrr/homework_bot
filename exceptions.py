class MissingCostantException(Exception):
    """Any of the vital constants not found."""

    pass


class ExpectedDictException(Exception):
    """API answer must be dict type."""

    pass
