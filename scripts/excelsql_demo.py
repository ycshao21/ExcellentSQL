import asyncio
from dotenv import load_dotenv
from excelsql.utils.log import logger

from excelsql.excelsql import ExcelSQL

app = ExcelSQL()


async def demo():
    excel_path = "data/users.xlsx"
    app.upload_excel(excel_path)

    query = ""
    logger.info(f"用户输入：{query}")

    normalized_query = app.normalize_query(query)
    logger.info(f"标准化后的查询：{normalized_query}")

    results = app.generate_sqls_and_check(
        query=normalized_query,
        concurrent=True,
    )
    logger.info(f"SQL生成结果：{results}")

    sql = app.poll_sqls(results)
    logger.info(f"最终的SQL：{sql}")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(demo())
