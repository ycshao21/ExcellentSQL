import re
import os
from .base_agent import BaseClient


def parse_response(response: str):
    result_match = re.search(r"Result:\s*(.*?)(?=\nMATCH:|\Z)", response, re.DOTALL)
    result = result_match.group(1).strip() if result_match else ""

    return result


class CheckAgent(BaseClient):
    async def run(self, sql: str):
        system_prompt = f"""
        您是一个 SQL 语句检查器。您的任务是使用 MCP Server 中的工具execute_query执行给定的 SQL 语句，获取查询结果。

        示例 1:
        任务：查找 2020 年后入职的所有员工
        SQL: SELECT * FROM employees WHERE join_date > '2020-01-01'
        结果：[员工列表]

        示例 2:
        任务：计算员工的平均薪资
        SQL: SELECT AVG(salary) FROM employees WHERE department = 'Sales'
        结果：错误：表 'employees' 中不存在 'department' 列

        请按以下格式填写您的回答：
        Result: <查询结果>
        """
        base_query = f"""
        SQL Query: {sql}
        """

        response = await self.process_query(base_query, system_prompt=system_prompt)
        result = parse_response(response)

        return result


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def main():
        check = CheckAgent()
        await check.connect_to_server(
            command="uvx",
            args=[
                "--from",
                "mcp-alchemy==2025.04.16.110003",
                "--with",
                "pymysql",
                "--refresh-package",
                "mcp-alchemy",
                "mcp-alchemy",
            ],
            env={"DB_URL": os.getenv("DB_URL")},
        )

        await check.run(
            description="查询用户yqxv2的邮箱",
            # sql="SELECT * FROM users WHERE username = 'yqxv2'"
            sql="SELECT * FROM email WHERE username = 'yqxv2';",
        )

        await check.cleanup()

    asyncio.run(main())
