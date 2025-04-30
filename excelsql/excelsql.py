import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from .query_normalizer import QueryNormalizer
from .agents.sql_agent import SQLAgent

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
    column_info = {}
    for column in df.columns:
        column_info[column] = {
            "type": str(df[column].dtype),
            "unique_values": list(df[column].unique()),
        }
    return column_info


class ExcelSQL:
    def __init__(self, num_generators: int = 5):
        self.query_normalizer = QueryNormalizer(model="gpt-4o-mini")
        self.sql_generators = [SQLAgent() for _ in range(num_generators)]
        self.document_generator = None
        self.ddl_generator = None

        self.active_document = None

    def upload_excel(self, file_path: str) -> bool:
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
        logger.info(f"表格文档已生成，保存至")
        del column_info

        # 生成DDL
        ddl = self.ddl_generator(table_name, document)
        logger.info(f"DDL已生成，保存至")

        # 执行DDL，将表格数据和文档上传到数据库

        logger.info(f"成功上传Excel数据至数据库")

        # 自动将当前表格设置为活动表格
        self.active_document = document
        return True

    # def set_active_table(self, table_name: str):
    #     self.active_document = _get_document(table_name)

    def normalize_query(self, query: str) -> str:
        return self.query_normalizer.normalize(query)

    def generate_sqls_and_check(
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

    def _generate_sql_and_check(self, query: str, document: str, idx: int = 0) -> str:
        sql = self.sql_generators[idx].generate_sql(query, document)
        flag, denotation = self._check_sql(sql)
        return {
            "sql": sql,
            "flag": flag,
            "denotation": denotation,
        }

    def poll_sqls(self, sqls: list) -> list:
        # TODO: 根据结果进行排序
        return sqls[0]
