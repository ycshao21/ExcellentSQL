import os
import pandas as pd
from pathlib import Path
import hydra
from omegaconf import DictConfig
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, text
from .query_normalizer import QueryNormalizer
from .agents.sql_agent import SQLAgent
from .agents.check_agent import CheckAgent
from .ddl_generator import DDLGenerator
from .document_generator import DocumentGenerator
from .utils.log import logger
from .utils.sort import Sort


def _extract_table_name(file_path: str) -> str:
    # 从文件路径中提取文件名，同时处理Windows和Unix风格的路径
    file_name = os.path.basename(file_path)  # 使用os.path.basename正确提取文件名

    # 去掉扩展名
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

        # 创建数据库引擎
        self.db_engine = create_engine(db_url)

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
        """
        将用户输入转化为标准的陈述句

        args:
            query (str): 用户输入的原始语句

        return:
            str: 转换后的标准化语句
        """
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

        try:
            with self.db_engine.connect() as connection:
                result = connection.execute(text(sql))

                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()

                    result_data = [dict(zip(columns, row)) for row in rows]
                else:
                    result_data = {"affected_rows": result.rowcount}

                return {"sql": sql, "flag": True, "denotation": result_data}
        except Exception as e:
            return {"sql": sql, "flag": False, "denotation": f"执行错误: {str(e)}"}

    def _check_sql(self, sql: str) -> tuple:
        """
        检查SQL语句的正确性
        
        args:
            sql (str): 要检查的SQL语句

        return:
            tuple: (执行状态, 执行结果)
        """
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
        """
        并行或串行重新生成多条SQL语句

        args:
            query (str): 查询语句
            sql (str): 失败的SQL语句
            error (str): 错误信息
            concurrent (bool): 是否并行生成
            
        return:
            list: 包含SQL、执行状态和结果的字典列表
        """
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
        """
        重新生成单条SQL并检查其正确性

        args:
            query (str): 查询语句
            document (str): 文档信息
            sql (str): 失败的SQL语句
            error (str): 错误信息
            idx (int): SQL生成器索引
            
        return:
            dict: 包含SQL、执行状态和结果的字典
        """
        # 初始化CheckAgent（如果尚未初始化）
        if not self.check_agent:
            self.check_agent = CheckAgent()
            
        # 生成上下文信息
        context = f"之前的SQL执行失败: {sql}\n错误信息: {error}"
        
        # 使用check_agent或SQL生成器修复SQL
        if idx == 0 and self.check_agent:  # 第一个生成器使用CheckAgent的修复
            regenerated_sql = self.check_agent.fix_sql(query, document, sql, error)
            if not regenerated_sql:  # 如果CheckAgent修复失败，则使用普通生成器
                regenerated_sql = self.sql_generators[idx].generate_sql(query, document, context)
        else:  # 其他生成器直接使用普通生成器
            regenerated_sql = self.sql_generators[idx].generate_sql(query, document, context)

        # 检查SQL的有效性
        try:
            with self.db_engine.connect() as connection:
                result = connection.execute(text(regenerated_sql))

                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()

                    result_data = [dict(zip(columns, row)) for row in rows]
                else:
                    result_data = {"affected_rows": result.rowcount}

                return {"sql": regenerated_sql, "flag": True, "denotation": result_data}
        except Exception as e:
            return {"sql": regenerated_sql, "flag": False, "denotation": f"执行错误: {str(e)}"}

    def poll_sqls(self, sqls: list) -> tuple:
        sorter = Sort(sqls)
        sorted_sqls = sorter.sort_by_result_frequency()

        sql = sorted_sqls[0]["sql"]
        flag = sorted_sqls[0]["flag"]
        denotation = sorted_sqls[0]["denotation"]

        return sql, flag, denotation
