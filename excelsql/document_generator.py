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
您是一位专业的数据分析师和文档编写专家。您的任务是根据提供的表格名称和列信息，使用清晰、专业的语言撰写一份详细的数据库表格文档，以便开发人员和数据分析师理解和使用该表格。

请遵循以下规则：
1. 为表格提供一个简洁明了的描述，说明其用途
2. 分析每个列的数据类型和唯一值，推断其用途和含义
3. 输出普通文本即可，不要使用Markdown格式
4. 无需识别主键和外键，您只分析一张表格
5. 无需给出数据存储方面的修改建议，你只负责根据实际数据写文档
6. 如果表格列名没有实义，请你根据数据进行合理的命名
7. 如果字段有确定的取值范围，请使用取值范围；否则，请使用取值示例

请严格按以下模板生成文档：
```
表格文档：<表格名称>

表格描述：
<表格用途>

字段详细信息：
<序号>. <字段名>
    - 字段名语言：<字段名语言>
    - 数据类型：<数据类型>
    - 取值范围/取值示例：<取值范围/取值示例>
    - 字段描述：<字段描述>

...
```
"""

USER_PROMPT = {
    "DocumentGenerator": {},
}

USER_PROMPT["DocumentGenerator"][
    "zh"
] = """
请根据以下信息生成表格文档：

表名：{table_name}
字段信息：
```
{column_info}
```

请按照规定格式输出一份详细的数据库表格文档。
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
