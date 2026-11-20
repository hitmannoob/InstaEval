"""Configuration helpers for the local InstaEval server."""


_DEBUG_VALUES = {"1", "true", "yes"}


def debug_mode_enabled(value):
    """Enable Flask's interactive debugger only for an explicit opt-in value."""
    return isinstance(value, str) and value.strip().lower() in _DEBUG_VALUES
