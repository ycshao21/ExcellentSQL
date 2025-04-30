import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from colorama import Fore, Back, Style, init

# 初始化colorama
init(autoreset=True)

# 统计数据
statistic_data = {"llm_call": 0}


class ColoredFormatter(logging.Formatter):
    """使用colorama实现的彩色日志格式化器"""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        # 创建记录的副本，避免修改原始记录
        # 这样可以防止颜色代码被保存到日志记录中
        record_copy = logging.makeLogRecord(record.__dict__)

        # 添加颜色到级别名称
        if record_copy.levelname in self.COLORS:
            record_copy.levelname = f"{self.COLORS[record_copy.levelname]}{record_copy.levelname}{Style.RESET_ALL}"

        # 为消息添加颜色
        if record_copy.levelno >= logging.CRITICAL:
            record_copy.msg = (
                f"{Fore.RED}{Style.BRIGHT}{record_copy.msg}{Style.RESET_ALL}"
            )
        elif record_copy.levelno >= logging.ERROR:
            record_copy.msg = f"{Fore.RED}{record_copy.msg}{Style.RESET_ALL}"
        elif record_copy.levelno >= logging.WARNING:
            record_copy.msg = f"{Fore.YELLOW}{record_copy.msg}{Style.RESET_ALL}"
        elif record_copy.levelno >= logging.INFO:
            record_copy.msg = f"{Fore.GREEN}{record_copy.msg}{Style.RESET_ALL}"
        elif record_copy.levelno >= logging.DEBUG:
            record_copy.msg = f"{Fore.BLUE}{record_copy.msg}{Style.RESET_ALL}"

        # 调用父类的format方法处理副本
        return super().format(record_copy)


def setup_logger(name="ExcelSQL", log_level=logging.INFO, log_dir="logs", colored=True):
    """
    设置logger，同时输出到控制台和文件

    Args:
        name (str): logger名称
        log_level (int): 日志级别
        log_dir (str): 日志文件目录
        colored (bool): 是否在控制台使用彩色输出

    Returns:
        logging.Logger: 配置好的logger对象
    """
    # 创建logger
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(log_level)

    # 如果logger已经有处理器，则不重复添加
    if logger.handlers:
        return logger

    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True, parents=True)

    # 日志格式
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    if colored:
        # 使用彩色格式化器
        colored_formatter = ColoredFormatter(
            fmt=log_format,
            datefmt=date_format,
        )
        console_handler.setFormatter(colored_formatter)
    else:
        # 使用普通格式化器
        plain_formatter = logging.Formatter(
            fmt=log_format,
            datefmt=date_format,
        )
        console_handler.setFormatter(plain_formatter)

    logger.addHandler(console_handler)

    # 文件处理器 (使用RotatingFileHandler自动轮转日志文件)
    # 文件中不使用彩色，避免ANSI转义序列污染日志文件
    file_formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format,
    )

    file_handler = RotatingFileHandler(
        filename=log_path / f"{name}.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# 创建默认logger
logger = setup_logger()


def get_logger(name=None, colored=True):
    """
    获取logger的辅助函数

    Args:
        name (str, optional): 子logger名称，如果提供，将创建一个ExcelSQL.{name}的logger
        colored (bool): 是否在控制台使用彩色输出

    Returns:
        logging.Logger: logger对象
    """
    if name:
        return setup_logger(f"ExcelSQL.{name}", colored=colored)
    return logger
