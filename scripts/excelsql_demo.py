from dotenv import load_dotenv
import hydra
from omegaconf import DictConfig

from excelsql.utils.log import logger
from excelsql.excelsql import ExcelSQL


@hydra.main(
    version_base="1.3",
    config_path="../config",
    config_name="main",
)
def demo(cfg: DictConfig):
    app = ExcelSQL(cfg)

    app.upload_excel(cfg.excel_path)

    query = "一共有多少学历为硕士的用户？"
    logger.info(f"用户输入：{query}")

    normalized_query = app.normalize_query(query)
    logger.info(f"标准化后的查询：{normalized_query}")

    results = app.generate_sqls_and_check(
        query=normalized_query,
        concurrent=cfg.concurrent,
    )
    logger.info(f"SQL生成结果：{results}")

    sql = app.poll_sqls(results)
    logger.info(f"最终的SQL：{sql}")


if __name__ == "__main__":
    load_dotenv()
    demo()
