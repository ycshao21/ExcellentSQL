import os
from openai import OpenAI

SYSTEM_PROMPT = {
    "SQLAgent_generate": {},
}

SYSTEM_PROMPT["SQLAgent_generate"][
    "cn"
] = """
您是专为 Text-to-SQL 系统设计的 SQL 生成专家。您的任务是根据用户提供的任务描述和相关信息，生成准确、简洁的 SQL 查询语句。输出必须严格为纯 SQL 语句，不包含任何注释、说明、Markdown 格式或其他非 SQL 内容，以确保直接解析和执行。
"""
SYSTEM_PROMPT["SQLAgent_generate"][
    "en"
] = """
You are an SQL generation expert designed for Text-to-SQL systems. Your task is to generate precise and concise SQL queries based on the user's task description and additional information. The output must strictly be a pure SQL statement, with no comments, explanations, Markdown formatting, or any non-SQL content, to ensure seamless parsing and execution.
"""

USER_PROMPT = {
    "SQLAgent_generate": {},
}
USER_PROMPT["SQLAgent_generate"][
    "cn"
] = """
请为以下任务生成 SQL 查询：
任务描述：{task}
文档信息：{document}
输出要求：仅返回纯 SQL 语句，不包含任何注释、说明或格式化内容。
"""
USER_PROMPT["SQLAgent_generate"][
    "en"
] = """
Please generate an SQL query for the following task:
Task: {task}
Document: {document}
Output Requirement: Return only the pure SQL statement, without any comments, explanations, or formatting.
"""


class SQLAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model = "deepseek-v3-250324"
        self.language = os.getenv("LANGUAGE", "en")

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
        system_prompt = SYSTEM_PROMPT["SQLAgent_generate"][self.language]

        user_prompt = USER_PROMPT["SQLAgent_generate"][self.language].format(
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
