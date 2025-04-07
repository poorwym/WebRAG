import logging
import os
from datetime import datetime


def setup_logger(name="webrag", log_level=logging.INFO):
    """
    设置一个同时输出到控制台和文件的logger
    
    Args:
        name: logger名称
        log_level: 日志级别
        
    Returns:
        配置好的logger实例
    """
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除已有的handlers，避免重复
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 创建文件handler，文件名带时间戳
    log_dir = os.path.join("data", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    
    # 设置日志格式，使用提供的示例格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# 使用示例
if __name__ == "__main__":
    logger = setup_logger("test")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")



