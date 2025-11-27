"""
Professional logging system
Provides structured logging, log rotation, error tracking, and other features
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
import traceback
import json
import asyncio
import time
import functools

class JSONFormatter(logging.Formatter):
    """JSON format log formatter"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'guild_id'):
            log_entry['guild_id'] = record.guild_id
        if hasattr(record, 'command'):
            log_entry['command'] = record.command
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
            
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """Colored console log formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        try:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # Format time (with exception handling)
            try:
                record.asctime = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            except:
                record.asctime = str(record.created)
            
            # Colored format
            formatted = f"{color}[{record.levelname}]{reset} {record.asctime} - {color}{record.name}{reset} - {record.getMessage()}"
            
            if record.exc_info:
                try:
                    formatted += f"\n{self.formatException(record.exc_info)}"
                except:
                    formatted += f"\n{str(record.exc_info)}"
                    
            return formatted
        except:
            # If formatting fails, return simple format
            return f"{record.levelname} - {record.name} - {record.getMessage()}"

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_json: bool = False,
    enable_console_color: bool = True
) -> None:
    """
    Set up the application's logging system
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Log file directory
        max_file_size: Maximum size of a single log file (bytes)
        backup_count: Number of log files to retain
        enable_json: Whether to enable JSON format logging
        enable_console_color: Whether to enable colored console output
    """
    
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # === Console handler ===
    console_handler = logging.StreamHandler(sys.stdout)
    if enable_console_color and sys.stdout.isatty():
        console_formatter = ColoredFormatter()
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # Console only shows INFO and above
    root_logger.addHandler(console_handler)
    
    # === File handler - regular logs ===
    log_file = os.path.join(log_dir, 'bot.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    if enable_json:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)  # File records all logs
    root_logger.addHandler(file_handler)
    
    # === Error log handler ===
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d\n'
        'Message: %(message)s\n'
        'Exception: %(exc_text)s\n'
        '=' * 80 + '\n'
    )
    
    error_handler.setFormatter(error_formatter)
    error_handler.setLevel(logging.ERROR)  # Only record errors
    root_logger.addHandler(error_handler)
    
    # Disable verbose logging from third-party libraries
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Log system initialization
    logger = logging.getLogger('utils.logger')
    logger.info(f"Logging system initialized - Level: {log_level}, Directory: {log_dir}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name, typically use __name__
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

class CommandLogger:
    """Command execution logger"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_command(
        self,
        command: str,
        user_id: int,
        guild_id: Optional[int],
        execution_time: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Log command execution
        
        Args:
            command: Name of the executed command
            user_id: User ID who executed the command
            guild_id: Guild/server ID (if any)
            execution_time: Execution time (milliseconds)
            success: Whether execution was successful
            error: Error message (if any)
        """
        extra = {
            'command': command,
            'user_id': user_id,
            'guild_id': guild_id or 'DM',
            'execution_time': round(execution_time, 2)
        }
        
        if success:
            self.logger.info(f"Command executed successfully", extra=extra)
        else:
            self.logger.error(f"Command execution failed: {error}", extra=extra)

def log_performance(func):
    """
    Performance monitoring decorator
    Records function execution time
    """
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            if execution_time > 1000:  # Log warning for operations over 1 second
                logger.warning(f"{func.__name__} execution time: {execution_time:.2f}ms")
            else:
                logger.debug(f"{func.__name__} execution time: {execution_time:.2f}ms")
                
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} execution failed (time: {execution_time:.2f}ms): {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            if execution_time > 1000:
                logger.warning(f"{func.__name__} execution time: {execution_time:.2f}ms")
            else:
                logger.debug(f"{func.__name__} execution time: {execution_time:.2f}ms")
                
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} execution failed (time: {execution_time:.2f}ms): {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper 