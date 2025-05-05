import os
import json
from openai import OpenAI
from .utils.log import logger

SYSTEM_PROMPT = {
    "DocumentGenerator": {},
}

SYSTEM_PROMPT["DocumentGenerator"][
    "zh"
] = """
您是一位专业的数据分析师和文档编写专家。您的任务是根据提供的表格名称和列信息，使用清晰、专业的语言撰写一份详细的数据库表格文档。

请遵循以下规则：
1. 为表格提供一个简洁明了的描述，说明其用途
2. 分析每个列的数据类型和唯一值，推断其用途和含义
3. 输出普通文本即可，不要使用Markdown格式
4. 无需识别主键和外键，您只分析一张表格
5. 无需给出数据存储方面的修改建议，你只负责根据实际数据写文档
6. 如果表格列名没有实义，请你根据数据进行合理的命名

您的输出应该是一个结构化的文档，详细描述表格的结构和用途，以便开发人员和数据分析师理解和使用该表格。
"""

SYSTEM_PROMPT["DocumentGenerator"][
    "en"
] = """
Please write a detailed database table document based on the provided table name and column information.

Please follow these rules:
1. Provide a clear and concise description of the table's purpose
2. Analyze the data type and unique values of each column to infer its purpose and meaning
3. Output plain text only, do not use Markdown format
4. Do not identify primary keys and foreign keys, you only analyze one table
5. Do not provide data storage-related modification suggestions, you only write documents based on actual data
6. If the table column name does not have meaning, please name it reasonably based on the data

Your output should be a structured document that provides a detailed description of the table's structure and purpose, enabling developers and data analysts to understand and use the table.
"""

USER_PROMPT = {
    "DocumentGenerator": {},
}

USER_PROMPT["DocumentGenerator"][
    "zh"
] = """
请根据以下信息生成表格文档：

表名：{table_name}
列信息：{column_info}

请提供一份详细的表格文档，包括表格描述和每个列的详细信息。
"""

USER_PROMPT["DocumentGenerator"][
    "en"
] = """
Please generate a table document based on the following information:

Table name: {table_name}
Column information: {column_info}

Please provide a detailed table document, including table description and detailed information for each column.
"""


class DocumentGenerator:
    def __init__(
        self,
        model: str,
        limit_value: int = -1,
    ):
        """
        初始化DocumentGenerator
        """
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model = model
        self.limit_value = limit_value
        logger.info(f"DocumentGenerator初始化完成，使用模型：{self.model}")

    def generate(
        self,
        table_name: str,
        column_info: dict,
        language: str = "zh",
    ) -> str:
        """
        根据表名和列信息生成表格文档

        args:
            table_name (str): 表名
            column_info (dict): 列信息，包含每列的数据类型和唯一值

        return:
            str: 生成的表格文档
        """
        logger.info(f"开始为表 {table_name} 生成文档")

        column_info_str = "| 列名 | 数据类型 | 唯一值示例 |\n| --- | --- | --- |\n"
        for column, info in column_info.items():
            unique_values = [str(v) for v in info["unique_values"]]
            if self.limit_value > 0:
                unique_values = unique_values[: self.limit_value]
            unique_values_str = ", ".join(unique_values)

            if self.limit_value > 0 and len(info["unique_values"]) > self.limit_value:
                unique_values_str += f" (等{len(info['unique_values'])}个)"
            column_info_str += f"| {column} | {info['type']} | {unique_values_str} |\n"

        system_prompt = SYSTEM_PROMPT["DocumentGenerator"][language]
        user_prompt = USER_PROMPT["DocumentGenerator"][language].format(
            table_name=table_name,
            column_info=column_info_str,
        )

        try:
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

            document = response.choices[0].message.content.strip()
            return document

        except Exception as e:
            logger.error(f"生成表格文档时发生错误: {e}")
            return f"Error generating document: {str(e)}"

    def __call__(self, table_name: str, column_info: dict) -> str:
        """
        使DocumentGenerator实例可调用

        args:
            table_name (str): 表名
            column_info (dict): 列信息，包含每列的数据类型和唯一值

        return:
            str: 生成的表格文档
        """
        return self.generate(table_name, column_info)
