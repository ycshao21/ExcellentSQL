import asyncio
from dotenv import load_dotenv
from utils import logger

from .excelsql import ExcelSQL


async def main():
    excelsql = ExcelSQL()

    excel_path = "data.xlsx"
    excelsql.upload_excel(excel_path)

    query = ""
    logger.info(f"用户输入：{query}")

    normalized_query = excelsql.normalize_query(query)
    logger.info(f"标准化后的查询：{normalized_query}")

    results = excelsql.generate_sqls_and_check(
        query=normalized_query,
        document=excelsql.active_document,
        concurrent=True,
    )

    sql = excelsql.poll_sqls(results)
    logger.info(f"生成的SQL：{sql}")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
