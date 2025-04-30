import json
import os

from .check_agent import CheckAgent
from .sql_agent import SQLAgent


class TaskManager:
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.check_agent = CheckAgent()

        self.final_sql = ""
        self.final_result = ""

        self.save_path = "./outputs/tasks_{query_idx}.json"

    def _save_tasks(self, tasks, query_idx=None):
        """保存任务到文件"""
        save_path = self.save_path.format(query_idx=query_idx)
        # 确保输出目录存在
        output_dir = os.path.dirname(save_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)

    async def execute_tasks(self, tasks: dict, context: str, query_idx=None):
        """执行所有任务并保存结果"""
        descriptions = [task["description"] for task in tasks.values()]
        sqls = []
        # 用于存储中间过程的列表
        intermediate_steps = []

        for i, (task_id, _) in enumerate(tasks.items()):
            description = descriptions[i]
            print(f"执行任务: {task_id} - {description}")

            # 第一次生成sql没有额外信息
            sql = self.sql_agent.generate_sql(
                descriptions=descriptions,
                prev_sqls=sqls,
                index=i,
                context=context,
            )
            tasks[task_id]["sql"] = sql
            sqls.append(sql)
            print(f"对于任务 {description} 生成的SQL: {sql}")

            # 记录初始SQL生成
            intermediate_steps.append(
                {
                    "type": "initial_generation",
                    "task_id": task_id,
                    "description": description,
                    "sql": sql,
                }
            )

            try:
                await self.check_agent.connect_to_server(
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

                max_attempts = 3
                current_sql = sql
                for attempt in range(max_attempts):
                    result, is_match, check_completed, adjustment = (
                        await self.check_agent.run(description, current_sql)
                    )

                    # 记录每次检查结果
                    step_info = {
                        "type": "check",
                        "task_id": task_id,
                        "attempt": attempt + 1,
                        "sql": current_sql,
                        "is_match": is_match,
                        "check_completed": check_completed,
                        "adjustment": adjustment if not is_match else "无需调整",
                    }

                    if is_match:
                        tasks[task_id]["sql"] = current_sql
                        tasks[task_id]["result"] = result
                        step_info["result"] = result
                        intermediate_steps.append(step_info)
                        print(f"Current SQL: {current_sql}")
                        break
                    else:
                        intermediate_steps.append(step_info)
                        current_sql = self.sql_agent.adjust_sql(current_sql, adjustment)
                        # 记录SQL调整
                        intermediate_steps.append(
                            {
                                "type": "adjustment",
                                "task_id": task_id,
                                "attempt": attempt + 1,
                                "sql": current_sql,
                                "previous_sql": step_info["sql"],
                                "adjustment": adjustment,
                            }
                        )
                        tasks[task_id]["sql"] = current_sql
                        print(f"第{attempt + 1}次调整后的SQL: {current_sql}")
            except Exception as e:
                print(f"执行任务 {task_id} 时出错: {str(e)}")
                error_msg = f"错误: {str(e)}"
                tasks[task_id]["result"] = error_msg
                # 记录错误
                intermediate_steps.append(
                    {
                        "type": "error",
                        "task_id": task_id,
                        "description": description,
                        "error": error_msg,
                    }
                )

            self._save_tasks(tasks, query_idx)

        await self.check_agent.cleanup()

        print("所有任务执行完毕")

        self.final_sql = tasks[list(tasks.keys())[-1]]["sql"]
        self.final_result = tasks[list(tasks.keys())[-1]]["result"]
        return (self.final_sql, self.final_result, intermediate_steps)


if __name__ == "__main__":
    import asyncio

    manager = TaskManager()
    asyncio.run(manager.execute_tasks())
    print(manager.final_sql)
