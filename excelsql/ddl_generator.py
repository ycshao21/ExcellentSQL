import os
from openai import OpenAI
from .utils.log import logger

SYSTEM_PROMPT = {
    "DDLGenerator": {},
}

SYSTEM_PROMPT["DDLGenerator"][
    "zh"
] = """
您是一位专业的数据库架构师，精通SQL DDL（数据定义语言）。您的任务是根据提供的表格名称和表格文档信息，生成创建表的DDL语句。

请遵循以下规则：
1. 根据文档中的字段信息，为每个字段选择最合适的数据类型
2. 使用标准SQL语法，确保DDL语句可以在主流数据库系统中执行
3. 仅输出纯SQL DDL语句，不要包含任何解释或注释
4. 请不要为表格添加主键、外键等约束

您的输出应该是一个完整的CREATE TABLE语句，可以直接执行以创建表结构。
"""

SYSTEM_PROMPT["DDLGenerator"][
    "en"
] = """
You are a professional database architect with expertise in SQL DDL (Data Definition Language). Your task is to generate a DDL statement to create a table based on the provided table name and table documentation.

Please follow these rules:
1. Choose the most appropriate data type for each field based on the information in the document
2. Use standard SQL syntax to ensure the DDL statement can be executed in mainstream database systems
3. Output only the pure SQL DDL statement, without any explanations or comments
4. Do not add any constraints such as primary keys or foreign keys to the table

Your output should be a complete CREATE TABLE statement that can be directly executed to create the table structure.
"""

USER_PROMPT = {
    "DDLGenerator": {},
}

USER_PROMPT["DDLGenerator"][
    "zh"
] = """
请根据以下信息生成创建表的DDL语句：

表名：{table_name}
表格文档：{document}

请仅返回纯SQL DDL语句，不包含任何解释或注释。
"""

USER_PROMPT["DDLGenerator"][
    "en"
] = """
Please generate a DDL statement to create a table based on the following information:

Table name: {table_name}
Table document: {document}

Please return only the pure SQL DDL statement, without any explanations or comments.
"""


class DDLGenerator:
    def __init__(
        self,
        model,
    ):
        """
        初始化DDLGenerator
        """
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model = model
        logger.info(f"DDLGenerator初始化完成，使用模型：{self.model}")

    def generate(
        self,
        table_name: str,
        document: str,
        language: str = "zh",
    ) -> str:
        """
        根据表名和文档信息生成DDL语句

        args:
            table_name (str): 表名
            document (str): 表格文档信息

        return:
            str: 生成的DDL语句
        """
        logger.info(f"开始为表 {table_name} 生成DDL语句")

        system_prompt = SYSTEM_PROMPT["DDLGenerator"][language]
        user_prompt = USER_PROMPT["DDLGenerator"][language].format(
            table_name=table_name,
            document=document,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        ddl = response.choices[0].message.content.strip()
        return ddl

    def __call__(self, table_name: str, document: str) -> str:
        """
        使DDLGenerator实例可调用

        args:
            table_name (str): 表名
            document (str): 表格文档信息

        return:
            str: 生成的DDL语句
        """
        return self.generate(table_name, document)
