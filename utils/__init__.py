"""
工具模块
包含日志、错误处理、命令系统等核心工具
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
    # 提供默认的空实现
    __all__ = []