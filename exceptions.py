class MissingCostantException(Exception):
    """Any of the vital constants not found."""

    pass


class NotExpectedHwStatusException(Exception):
    """API answer contains unknown Hw status."""

    pass


class NotOkResponseExeption(Exception):
    """Request got not OK Status."""

    pass


""" Не понял мысль: Для первых двух удобно завести общий базовый
класс и делать его перехват в main().
"""
