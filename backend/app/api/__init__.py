"""API routers package."""

# Using try-except to prevent circular imports when the app is starting up
try:
    from . import sentiment
except ImportError:
    pass

try:
    from . import backtest
except ImportError:
    pass 