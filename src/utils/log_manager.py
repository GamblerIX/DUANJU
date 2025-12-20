"""日志管理器实现 - Debug Version

This module provides comprehensive logging functionality for the debug version.
Includes file-based logging with rotation, console output, and specialized
logging methods for API requests, user actions, and cache operations.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class LogManager:
    """日志管理器 - 管理应用日志，支持文件和控制台输出，自动轮转"""
    
    DEFAULT_LOG_DIR = "logs"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    
    _instance: Optional['LogManager'] = None
    _logger: Optional[logging.Logger] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logger()
            self._setup_exception_hook()
            LogManager._initialized = True
    
    def _setup_logger(self) -> None:
        """初始化日志器"""
        self._logger = logging.getLogger("DuanjuApp")
        self._logger.setLevel(logging.DEBUG)
        
        if self._logger.handlers:
            return
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台使用简洁格式，不显示堆栈
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        # 过滤掉 ERROR 级别，避免重复输出
        console_handler.addFilter(lambda record: record.levelno < logging.ERROR)
        self._logger.addHandler(console_handler)
        
        # 错误输出使用友好格式（不含堆栈）
        error_console_formatter = logging.Formatter(
            '%(asctime)s - ⚠️ %(message)s',
            datefmt='%H:%M:%S'
        )
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(error_console_formatter)
        self._logger.addHandler(error_handler)
        
        log_dir = Path(self.DEFAULT_LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"duanju_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.MAX_FILE_SIZE,
            backupCount=self.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)
        
        error_log_file = log_dir / f"duanju_error_{datetime.now().strftime('%Y%m%d')}.log"
        error_file_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=self.MAX_FILE_SIZE,
            backupCount=self.BACKUP_COUNT,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(file_formatter)
        self._logger.addHandler(error_file_handler)
        
        self.info(f"DuanjuApp started at {datetime.now()}")
        self.info(f"Python version: {sys.version}")
    
    def _setup_exception_hook(self) -> None:
        """设置全局异常钩子"""
        def exception_hook(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            self._logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
        sys.excepthook = exception_hook
    
    def setup_qt_exception_hook(self) -> None:
        """设置 Qt 异常钩子"""
        try:
            from PySide6.QtCore import qInstallMessageHandler, QtMsgType
            
            def qt_message_handler(mode, context, message):
                # 过滤掉一些常见的无害警告
                if any(skip in message for skip in [
                    "startAngle", "endAngle", "IndeterminateProgressRing",
                    "QThread", "destroyed while thread"
                ]):
                    return  # 静默忽略
                
                if mode == QtMsgType.QtDebugMsg:
                    self.debug(f"Qt: {message}")
                elif mode == QtMsgType.QtInfoMsg:
                    self.debug(f"Qt: {message}")
                elif mode == QtMsgType.QtWarningMsg:
                    self.debug(f"Qt Warning: {message}")  # 降级为 debug
                elif mode == QtMsgType.QtCriticalMsg:
                    self.warning(f"Qt Critical: {message}")
                elif mode == QtMsgType.QtFatalMsg:
                    self.error(f"Qt Fatal: {message}")
            
            qInstallMessageHandler(qt_message_handler)
            self.debug("Qt message handler installed")
        except Exception as e:
            self.debug(f"Failed to install Qt message handler: {e}")
    
    def debug(self, message: str) -> None:
        """记录调试日志"""
        self._logger.debug(message)
    
    def info(self, message: str) -> None:
        """记录信息日志"""
        self._logger.info(message)
    
    def warning(self, message: str) -> None:
        """记录警告日志"""
        self._logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False) -> None:
        """记录错误日志"""
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False) -> None:
        """记录严重错误日志"""
        self._logger.critical(message, exc_info=exc_info)
    
    def exception(self, message: str) -> None:
        """记录异常日志（自动包含堆栈跟踪）"""
        self._logger.exception(message)
    
    def log_api_request(
        self, 
        url: str, 
        params: Optional[dict] = None,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """记录 API 请求日志"""
        msg = f"API Request: {url}"
        if params:
            msg += f" | Params: {params}"
        if status_code is not None:
            msg += f" | Status: {status_code}"
        if error:
            msg += f" | Error: {error}"
            self.error(msg)
        else:
            self.debug(msg)
    
    def log_api_response(
        self,
        url: str,
        status_code: int,
        success: bool,
        body_preview: str = ""
    ) -> None:
        """记录 API 响应日志"""
        if success:
            self.debug(f"API Response: {url} | Status: {status_code}")
        # 失败时不在这里输出，让上层服务统一处理错误日志
    
    def log_user_action(self, action: str, details: str = "") -> None:
        """记录用户操作日志"""
        msg = f"User Action: {action}"
        if details:
            msg += f" | {details}"
        self.info(msg)
    
    def log_error(self, error_type: str, message: str, details: str = "") -> None:
        """记录错误日志 - 控制台友好输出"""
        self._logger.error(f"[{error_type}] {message}")
        if details:
            self._logger.debug(f"Error details: {details}")
    
    def log_service_error(self, service: str, operation: str, error: Exception) -> None:
        """记录服务层错误 - 控制台友好输出，文件记录详细堆栈"""
        # 控制台友好信息
        friendly_msg = self.get_friendly_error_message(error)
        self._logger.error(f"[{service}] {friendly_msg}")
        # 详细信息只写入文件（通过 debug 级别）
        self._logger.debug(f"Service Error [{service}.{operation}]: {type(error).__name__}: {error}", exc_info=True)
    
    def log_ui_error(self, component: str, error: Exception) -> None:
        """记录 UI 层错误 - 控制台友好输出"""
        friendly_msg = self.get_friendly_error_message(error)
        self._logger.error(f"[{component}] {friendly_msg}")
        self._logger.debug(f"UI Error [{component}]: {type(error).__name__}: {error}", exc_info=True)
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = True) -> None:
        """记录缓存操作"""
        status = "HIT" if hit else "MISS"
        self.debug(f"Cache {operation}: {key} | {status}")
    
    def log_config_change(self, key: str, old_value, new_value) -> None:
        """记录配置变更"""
        self.info(f"Config Changed: {key} | {old_value} -> {new_value}")


    def get_friendly_error_message(self, error: Exception) -> str:
        """将异常转换为用户友好的错误信息"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 网络相关错误
        if "timeout" in error_str or "timeout" in error_type:
            return "请求超时，服务器响应过慢"
        if "refused" in error_str:
            return "连接被拒绝，服务器可能不可用"
        if "resolve" in error_str or "dns" in error_str or "name or service not known" in error_str:
            return "无法解析服务器地址，请检查网络"
        if "ssl" in error_str or "certificate" in error_str:
            return "SSL 证书验证失败"
        if "disconnect" in error_str or "connection" in error_str:
            return "网络连接断开，请检查网络后重试"
        
        # HTTP 错误
        if "404" in error_str:
            return "请求的资源不存在"
        if "403" in error_str:
            return "访问被拒绝"
        if "503" in error_str:
            return "服务暂时不可用，请稍后重试"
        if "500" in error_str or "502" in error_str:
            return "服务器内部错误，请稍后重试"
        
        # 解析错误
        if "json" in error_str or "parse" in error_str or "json" in error_type:
            return "数据解析失败，响应格式异常"
        
        # 默认返回原始错误信息（简化）
        msg = str(error)
        if len(msg) > 50:
            msg = msg[:50] + "..."
        return msg


logger = LogManager()


def get_logger() -> LogManager:
    """获取全局日志实例"""
    return logger
