import os
from openai import OpenAI

SYSTEM_PROMPT = {
    "SQLAgent": {},
}

SYSTEM_PROMPT["SQLAgent"][
    "zh"
] = """
您是专为 Text-to-SQL 系统设计的 SQL 生成专家。您的任务是根据用户提供的任务描述和相关信息，生成准确、简洁的 SQL 查询语句。

要求：
1. 输出必须严格为纯 SQL 语句，不包含任何注释、说明、Markdown 格式或其他非 SQL 内容，以确保直接解析和执行。
2. 文档中给出的表格名和字段名是实际数据库中的名称，请严格使用，不要进行任何修改，如翻译、同义词替换等。
3. 请确保 SQL 语句的语法正确，并符合 SQL 标准。
"""

USER_PROMPT = {
    "SQLAgent": {},
}
USER_PROMPT["SQLAgent"][
    "zh"
] = """
请为以下任务生成 SQL 查询：
任务描述：
```
{task}
```

文档信息：
```
{document}
```

输出要求：仅返回纯 SQL 语句，不包含任何注释、说明或格式化内容。
"""

class SQLAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model = "deepseek-v3-250324"
        self.language = "zh"

    def generate_sql(self, task: str, document: str) -> str:
        """
        function:
            Receive a string containing a task description and generate the corresponding SQL;
        args:
            task (str): task description
            document (str): document information
        return:
            str: SQL
        """
        system_prompt = SYSTEM_PROMPT["SQLAgent"][self.language]

        user_prompt = USER_PROMPT["SQLAgent"][self.language].format(
            task=task,
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

        sql = response.choices[0].message.content.strip()
        return sql
