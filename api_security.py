"""Request limits and origin policy for the locally hosted API."""

import re


_CHROME_EXTENSION_ORIGIN = re.compile(r"chrome-extension://[a-p]{32}\Z")
MAX_REQUEST_BYTES = 1024 * 1024


def is_allowed_request_origin(origin):
    """Allow non-browser local clients and Chrome extension requests only."""
    if origin is None:
        return True
    if not isinstance(origin, str):
        return False
    return _CHROME_EXTENSION_ORIGIN.fullmatch(origin) is not None
