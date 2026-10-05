"""Errors that can be safely presented to API clients."""


class DataError(ValueError):
    """Raised for missing, malformed, or inconsistent route data."""
