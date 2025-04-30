import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import logger, get_logger, setup_logger


def main():
    print("=== 彩色日志示例 ===")
    # 使用默认logger (彩色)
    logger.debug("这是一条调试日志")  # 默认不会显示，因为日志级别是INFO
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")

    # 使用子模块logger (彩色)
    sub_logger = get_logger("example")
    sub_logger.info("这是子模块的彩色日志")

    print("\n=== 无彩色日志示例 ===")
    # 创建无彩色logger
    plain_logger = setup_logger(name="PlainLogger", colored=False)
    plain_logger.info("这是无彩色的信息日志")
    plain_logger.warning("这是无彩色的警告日志")
    plain_logger.error("这是无彩色的错误日志")

    print("\n=== 调试级别日志示例 ===")
    # 创建DEBUG级别的logger
    debug_logger = setup_logger(name="DebugLogger", log_level=logging.DEBUG)
    debug_logger.debug("这是一条调试日志，现在可以显示了")
    debug_logger.info("这是一条信息日志")

    print("\n=== 在其他模块中使用logger ===")
    print("在其他模块中，可以直接导入logger使用:")
    print("from src.utils import logger")
    print("logger.info('在其他模块中使用logger')")

    print("\n或者创建特定模块的logger:")
    print("from src.utils import get_logger")
    print("module_logger = get_logger('module_name')")
    print("module_logger.info('模块特定的日志')")


if __name__ == "__main__":
    main()
