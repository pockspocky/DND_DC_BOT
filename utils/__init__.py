"""
Utility module
Contains core tools including logging, error handling, command system, etc.
"""

try:
    from .logger import get_logger, setup_logging
    from .error_handler import ErrorHandler, BotError, error_handler
    from .command_system import CommandRegistry, command_route, command_registry
    
    __all__ = [
        'get_logger', 
        'setup_logging', 
        'ErrorHandler', 
        'BotError',
        'error_handler',
        'CommandRegistry',
        'command_route',
        'command_registry'
    ]
except ImportError as e:
    print(f"Warning: Failed to import utils modules: {e}")
    # Provide default empty implementation
    __all__ = []