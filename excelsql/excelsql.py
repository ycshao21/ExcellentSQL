import os
import pandas as pd
from pathlib import Path
import hydra
from omegaconf import DictConfig
from concurrent.futures import ThreadPoolExecutor

from .query_normalizer import QueryNormalizer
from .agents.sql_agent import SQLAgent
from .agents.check_agent import CheckAgent
from .ddl_generator import DDLGenerator
from .document_generator import DocumentGenerator

from .utils.log import logger


def _extract_table_name(file_path: str) -> str:
    # 从文件路径中提取文件名
    table_name = file_path.split("/")[-1].split(".")[0]

    # 后处理
    table_name = table_name.lower()
    table_name = "_".join(table_name.split())

    # TODO: 数据库中检查是否已经存在该表名
    return table_name


def _extract_table_info(df: pd.DataFrame) -> str:
    if df.columns.empty:  # 表格没有列名
        df.columns = [f"Column_{i}" for i in range(df.shape[1])]

    column_info = {}
    for column in df.columns:
        column_info[column] = {
            "type": str(
                df[column].dtype
            ),  # FIXME: 字符串在 DataFrame 中以 object 类型存储
            "unique_values": list(df[column].unique()),
        }
    return column_info


class ExcelSQL:
    def __init__(self, cfg: DictConfig):
        self.query_normalizer = QueryNormalizer(**cfg.query_normalizer)
        self.sql_generators = [SQLAgent() for _ in range(cfg.num_generators)]
        self.document_generator = DocumentGenerator(**cfg.document_generator)
        self.ddl_generator = DDLGenerator(**cfg.ddl_generator)
        self.check_agent = None  # 将在需要时初始化

        self.active_document = None

    def upload_excel(self, file_path: str, save_to_local: bool = True) -> bool:
        # 读取Excel文件
        try:
            df: pd.DataFrame = pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"无法读取Excel文件: {e}")
            return False

        logger.info(f"已读取Excel文件: {file_path}")

        table_name = _extract_table_name(file_path)
        logger.info(f"表格名称: {table_name}")

        # 提取表格信息
        column_info = _extract_table_info(df)

        # 生成文档
        document = self.document_generator(table_name, column_info)
        logger.info(f"表格 {table_name} 文档已生成")

        local_output_dir = Path(
            hydra.core.hydra_config.HydraConfig.get()["runtime"]["output_dir"]
        )
        if save_to_local:
            doc_path = local_output_dir / f"{table_name}_doc.txt"
            with open(doc_path, "w") as f:
                f.write(document)
            logger.info(f"表格 {table_name} 文档已保存至 {doc_path}")

        del column_info

        # 生成DDL
        ddl = self.ddl_generator(table_name, document)
        logger.info(f"表格 {table_name} DDL已生成")

        if save_to_local:
            ddl_path = local_output_dir / f"{table_name}.sql"
            with open(ddl_path, "w") as f:
                f.write(ddl)
            logger.info(f"表格 {table_name} DDL已保存至 {ddl_path}")

        # TODO: 执行DDL，将表格数据和文档上传到数据库
        # logger.info(f"成功上传Excel数据至数据库")

        # 自动将当前表格设置为活动表格
        self.active_document = document
        return True

    # def set_active_table(self, table_name: str):
    #     self.active_document = _get_document(table_name)

    def normalize_query(self, query: str) -> str:
        """
        将用户输入转化为标准的陈述句

        args:
            query (str): 用户输入的原始语句

        return:
            str: 转换后的标准化语句
        """
        return self.query_normalizer.normalize(query)

    async def generate_sqls_and_check(
        self,
        query: str,
        concurrent: bool = True,
    ) -> str:
        if concurrent:
            with ThreadPoolExecutor() as executor:
                results = list(
                    executor.map(
                        self._generate_sql_and_check,
                        [query] * len(self.sql_generators),
                        [self.active_document] * len(self.sql_generators),
                        range(len(self.sql_generators)),
                    )
                )
        else:
            results = [
                self._generate_sql_and_check(query, self.active_document, idx)
                for idx in range(len(self.sql_generators))
            ]

        return results

    def _generate_sql_and_check(self, query: str, document: str, idx: int = 0) -> dict:
        """
        生成SQL并检查其正确性

        args:
            query (str): 查询语句
            document (str): 文档信息
            idx (int): SQL生成器索引

        return:
            dict: 包含SQL、执行状态和结果的字典
        """
        sql = self.sql_generators[idx].generate_sql(query, document)
        flag, denotation = self._check_sql(sql)
        return {
            "sql": sql,
            "flag": flag,
            "denotation": denotation,
        }

    async def _check_sql(self, sql: str) -> tuple:
        """
        检查SQL语句的正确性

        args:
            sql (str): 要检查的SQL语句

        return:
            tuple: (执行状态, 执行结果)
        """
        # 如果check_agent未初始化，则初始化它
        if self.check_agent is None:
            self.check_agent = CheckAgent()
            # 连接到数据库服务器
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
                logger.info("成功连接到数据库服务器")
            except Exception as e:
                logger.error(f"连接数据库服务器失败: {e}")
                return False, f"Error: {str(e)}"

        try:
            # 执行SQL并获取结果
            result = await self.check_agent.run(sql)
            return True, result
        except Exception as e:
            logger.error(f"执行SQL失败: {e}")
            return False, f"Error: {str(e)}"

    def poll_sqls(self, sqls: list) -> list:
        # TODO: 根据结果进行排序
        return sqls[0]
