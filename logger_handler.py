import logging
import os
import sys


def get_logger(name: str = "kk_card_tool", level=logging.INFO):
    """
    获取配置好的logger实例
    
    Args:
        name: logger名称，默认为None
        level: 日志级别，默认为logging.INFO
    
    Returns:
        logging.Logger: 配置好的logger实例
    """
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if not logger.handlers:
        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 文件输出
        # 确保日志目录存在
        # 判断是否为打包后的程序
        if getattr(sys, 'frozen', False):
            # 打包后的程序，使用可执行文件所在目录
            base_dir = os.path.dirname(sys.executable)
            log_path = os.path.join(base_dir, "kk_card_tool.log")

            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
