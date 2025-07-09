"""
专业日志系统
提供结构化日志记录、日志轮转、错误跟踪等功能
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
    """JSON格式的日志格式化器"""
    
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
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
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
    """彩色控制台日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        try:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # 格式化时间（添加异常处理）
            try:
                record.asctime = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            except:
                record.asctime = str(record.created)
            
            # 彩色格式
            formatted = f"{color}[{record.levelname}]{reset} {record.asctime} - {color}{record.name}{reset} - {record.getMessage()}"
            
            if record.exc_info:
                try:
                    formatted += f"\n{self.formatException(record.exc_info)}"
                except:
                    formatted += f"\n{str(record.exc_info)}"
                    
            return formatted
        except:
            # 如果格式化失败，返回简单格式
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
    设置应用程序的日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录
        max_file_size: 单个日志文件最大大小 (字节)
        backup_count: 保留的日志文件数量
        enable_json: 是否启用JSON格式日志
        enable_console_color: 是否启用控制台彩色输出
    """
    
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # === 控制台处理器 ===
    console_handler = logging.StreamHandler(sys.stdout)
    if enable_console_color and sys.stdout.isatty():
        console_formatter = ColoredFormatter()
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # 控制台只显示INFO以上
    root_logger.addHandler(console_handler)
    
    # === 文件处理器 - 常规日志 ===
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
    file_handler.setLevel(logging.DEBUG)  # 文件记录所有日志
    root_logger.addHandler(file_handler)
    
    # === 错误日志处理器 ===
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
    error_handler.setLevel(logging.ERROR)  # 只记录错误
    root_logger.addHandler(error_handler)
    
    # 禁用第三方库的详细日志
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # 记录日志系统初始化
    logger = logging.getLogger('utils.logger')
    logger.info(f"日志系统初始化完成 - 级别: {log_level}, 目录: {log_dir}")

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称，通常使用 __name__
        
    Returns:
        配置好的日志器实例
    """
    return logging.getLogger(name)

class CommandLogger:
    """命令执行日志记录器"""
    
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
        记录命令执行日志
        
        Args:
            command: 执行的命令名称
            user_id: 执行用户ID
            guild_id: 服务器ID（如果有）
            execution_time: 执行时间（毫秒）
            success: 是否执行成功
            error: 错误信息（如果有）
        """
        extra = {
            'command': command,
            'user_id': user_id,
            'guild_id': guild_id or 'DM',
            'execution_time': round(execution_time, 2)
        }
        
        if success:
            self.logger.info(f"命令执行成功", extra=extra)
        else:
            self.logger.error(f"命令执行失败: {error}", extra=extra)

def log_performance(func):
    """
    性能监控装饰器
    记录函数执行时间
    """
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            if execution_time > 1000:  # 超过1秒的操作记录警告
                logger.warning(f"{func.__name__} 执行耗时: {execution_time:.2f}ms")
            else:
                logger.debug(f"{func.__name__} 执行耗时: {execution_time:.2f}ms")
                
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} 执行失败 (耗时: {execution_time:.2f}ms): {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            if execution_time > 1000:
                logger.warning(f"{func.__name__} 执行耗时: {execution_time:.2f}ms")
            else:
                logger.debug(f"{func.__name__} 执行耗时: {execution_time:.2f}ms")
                
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} 执行失败 (耗时: {execution_time:.2f}ms): {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper 