import os
import pandas as pd
from pathlib import Path
import hydra
from omegaconf import DictConfig
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, text
from .query_normalizer import QueryNormalizer
from .agents.sql_agent import SQLAgent
from .ddl_generator import DDLGenerator
from .document_generator import DocumentGenerator
from .utils.log import logger
from .utils.sort import Sort


def _extract_table_name(file_path: str) -> str:
    file_name = os.path.basename(file_path)
    table_name = file_name.split(".")[0]
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
        db_url = os.getenv("DB_URL")
        if not db_url:
            logger.error("数据库连接URL未设置")
            return False

        self.db_engine = create_engine(db_url)
        self.query_normalizer = QueryNormalizer(**cfg.query_normalizer)
        self.sql_generators = [SQLAgent() for _ in range(cfg.num_generators)]
        self.document_generator = DocumentGenerator(**cfg.document_generator)
        self.ddl_generator = DDLGenerator(**cfg.ddl_generator)
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

        # 确保输出目录路径正确，并创建完整目录结构
        output_base_dir = "outputs"
        os.makedirs(output_base_dir, exist_ok=True)

        if save_to_local:
            # 创建完整文件路径
            document_dir = os.path.join(output_base_dir, "document")
            os.makedirs(document_dir, exist_ok=True)
            doc_path = os.path.join(document_dir, f"{table_name}.txt")

            # 保存文档
            with open(doc_path, "w") as f:
                f.write(document)
            logger.info(f"表格 {table_name} 文档已保存至 {doc_path}")

        del column_info

        # 生成DDL
        ddl = self.ddl_generator(table_name, document)
        logger.info(f"表格 {table_name} DDL已生成")

        if save_to_local:
            # 保存DDL文件
            ddl_dir = os.path.join(output_base_dir, "ddl")
            os.makedirs(ddl_dir, exist_ok=True)
            ddl_path = os.path.join(ddl_dir, f"{table_name}.sql")
            with open(ddl_path, "w") as f:
                f.write(ddl)
            logger.info(f"表格 {table_name} DDL已保存至 {ddl_path}")

        # 使用sqlalchemy执行DDL并上传数据
        try:
            # 执行DDL创建表
            with self.db_engine.connect() as connection:
                connection.execute(text(ddl))
                connection.commit()
                logger.info(f"表格 {table_name} 成功创建")

                # 将DataFrame数据上传到数据库
                # FIXME: to_sql也会创建表格，这里暂时用append模式
                df.to_sql(
                    name=table_name,
                    con=self.db_engine,
                    if_exists="append",
                    index=False,
                    chunksize=1000,
                )
                logger.info(f"成功上传Excel数据至数据库表 {table_name}")

        except Exception as e:
            logger.error(f"上传数据到数据库失败: {e}")
            return False

        return True

    def read_document(self, table_name: str):
        doc_path = f"outputs/document/{table_name}.txt"
        try:
            # 读取所有内容
            with open(doc_path, "r") as f:
                self.active_document = f.read()
                logger.info(f"已加载文档: {doc_path}")
        except FileNotFoundError:
            logger.error(f"文档 {doc_path} 不存在")

    def normalize_query(self, query: str) -> str:
        return self.query_normalizer.normalize(query)


    def generate_sqls_and_check(
        self,
        query: str,
        concurrent: bool = True,
    ) -> list:
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
        sql = self.sql_generators[idx].generate_sql(query, document)
        flag, denotation = self._check_sql(sql)
        return {"sql": sql, "flag": flag, "denotation": denotation}


    def _check_sql(self, sql: str) -> tuple:
        try:
            with self.db_engine.connect() as connection:
                result = connection.execute(text(sql))
                
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    result_data = [dict(zip(columns, row)) for row in rows]
                else:
                    result_data = {"affected_rows": result.rowcount}
                    
                return True, result_data
        except Exception as e:
            return False, f"执行错误: {str(e)}"

    def regenerate_sqls(
        self,
        query: str,
        sql: str,
        error: str,
        concurrent: bool = True,
    ) -> list:
        if concurrent:
            with ThreadPoolExecutor() as executor:
                results = list(
                    executor.map(
                        self._regenerate_sql,
                        [query] * len(self.sql_generators),
                        [self.active_document] * len(self.sql_generators),
                        [sql] * len(self.sql_generators),
                        [error] * len(self.sql_generators),
                        range(len(self.sql_generators)),
                    )
                )
        else:
            results = [
                self._regenerate_sql(query, self.active_document, sql, error, idx)
                for idx in range(len(self.sql_generators))
            ]

        return results

    def _regenerate_sql(self, query: str, document: str, sql: str, error: str, idx: int = 0) -> dict:
        context = f"之前执行失败的SQL: {sql}，执行时的错误信息: {error}"
        document = document + context
        regenerated_sql = self.sql_generators[idx].generate_sql(query, document)
        flag, denotation = self._check_sql(regenerated_sql)
        return {"sql": regenerated_sql, "flag": flag, "denotation": denotation}


    def poll_sqls(self, sqls: list) -> tuple:
        sorter = Sort(sqls)
        sorted_sqls = sorter.sort_by_result_frequency()

        sql = sorted_sqls[0]["sql"]
        flag = sorted_sqls[0]["flag"]
        denotation = sorted_sqls[0]["denotation"]

        return sql, flag, denotation


