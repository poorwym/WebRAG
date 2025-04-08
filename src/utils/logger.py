import logging
import os
from datetime import datetime
from typing import Dict, Optional


class Logger:
    """
    日志管理器类，使用单例模式确保全局唯一
    """
    _instances: Dict[str, "Logger"] = {}
    
    def __new__(cls, name: str = "webrag", log_level: int = logging.INFO) -> "Logger":
        """
        实现单例模式，确保同名logger只被创建一次
        """
        if name not in cls._instances:
            cls._instances[name] = super(Logger, cls).__new__(cls)
            cls._instances[name]._initialized = False
        return cls._instances[name]
    
    def __init__(self, name: str = "webrag", log_level: int = logging.INFO):
        """
        初始化日志管理器
        
        Args:
            name: logger名称
            log_level: 日志级别
        """
        # 避免重复初始化
        if getattr(self, "_initialized", False):
            return
            
        self.name = name
        self.log_level = log_level
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # 清除已有的handlers，避免重复
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 设置日志格式
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建控制台handler
        self._setup_console_handler(formatter)
        
        # 创建文件handler
        self._setup_file_handler(formatter)
        
        self._initialized = True
    
    def _setup_console_handler(self, formatter: logging.Formatter):
        """设置控制台日志处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self, formatter: logging.Formatter):
        """设置文件日志处理器"""
        # 获取绝对项目根目录路径（从__file__向上两级）
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, "data", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"{self.name}_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录严重错误日志"""
        self.logger.critical(message)
    
    @classmethod
    def get_logger(cls, name: str = "webrag") -> Optional["Logger"]:
        """
        获取已创建的logger实例
        
        Args:
            name: logger名称
            
        Returns:
            对应名称的Logger实例，如不存在则返回None
        """
        return cls._instances.get(name)


# 使用示例
if __name__ == "__main__":
    # 创建logger
    logger = Logger("test")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    # 演示单例模式
    same_logger = Logger("test")  # 获取同一个实例
    same_logger.info("这是同一个logger实例")
    
    # 创建另一个logger
    another_logger = Logger("another_test")
    another_logger.info("这是另一个logger实例")



