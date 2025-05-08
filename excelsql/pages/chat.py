# src/pages/2_Chat_with_File.py
import streamlit as st
import os
import pandas as pd
import sys

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 上传文件存储的目录
UPLOAD_DIR = "data"
DDL_DIR = "outputs/ddl"

# 设置页面配置
st.set_page_config(page_title="与文件聊天", page_icon="💬")

# 检查ExcelSQL实例是否已初始化
if "excel_sql_app" not in st.session_state or st.session_state.excel_sql_app is None:
    st.error("ExcelSQL应用未初始化，请返回主页重新启动应用")
    st.stop()

st.markdown("# 💬 与文件聊天")
st.sidebar.header("与文件聊天")
st.write("""选择一个已上传的 Excel 文件，然后输入您的问题。""")


# 获取上传文件列表
def get_uploaded_tables():
    """获取表格列表"""
    files = []
    if os.path.exists(DDL_DIR):
        try:
            files = [
                f.split(".")[0]  # 不含后缀
                for f in os.listdir(DDL_DIR)
                if os.path.isfile(os.path.join(DDL_DIR, f))
                # and f.lower().endswith((".xlsx", ".xls"))
                and f.lower().endswith(".sql")
            ]
        except Exception as e:
            st.error(f"读取目录 '{DDL_DIR}' 时出错: {e}")
    else:
        st.warning(f"目录 '{DDL_DIR}' 不存在。请先在上传文件页面上传文件。")
    return files


# SQL查询处理函数
def get_sql_response(user_question):
    st.info(f"用户问题: {user_question}")

    try:
        # 获取共享的ExcelSQL实例
        excel_sql_app = st.session_state.excel_sql_app

        excel_sql_app.read_document(selected_table)

        # 标准化查询
        normalized_query = excel_sql_app.normalize_query(user_question)
        st.write(f"标准化后的查询: {normalized_query}")

        # 生成SQL并执行
        results = excel_sql_app.generate_sqls_and_check(
            query=normalized_query,
            concurrent=True,
        )
        print(results)

        # 获取最终SQL和结果
        sql, flag, denotation = excel_sql_app.poll_sqls(results)
        
        # 检查SQL并在需要时重新生成
        max_attempts = 3  # 最大尝试次数
        current_attempt = 0
        check_flag = False
        check_result = None
        
        while current_attempt < max_attempts:
            try:
                # 检查SQL
                check_flag, check_result = excel_sql_app._check_sql(sql)
                
                if check_flag:  # SQL检查成功
                    denotation = check_result
                    break
                else:  # SQL检查失败，尝试重新生成
                    st.warning(f"SQL检查失败（尝试 {current_attempt+1}/{max_attempts}）: {check_result}")
                    
                    # 重新生成多条SQL
                    regen_results = excel_sql_app.regenerate_sqls(
                        query=normalized_query,
                        sql=sql,
                        error=str(check_result),
                        concurrent=True
                    )
                    
                    # 选择最佳SQL
                    if regen_results:
                        sql, check_flag, check_result = excel_sql_app.poll_sqls(regen_results)
                        
                        if check_flag:  # 找到有效SQL
                            denotation = check_result
                            break
                    
                    current_attempt += 1
            except Exception as e:
                st.error(f"SQL检查/重新生成过程中发生错误: {e}")
                import traceback
                st.error(traceback.format_exc())
                current_attempt += 1
                
        if not check_flag:
            st.error(f"在{max_attempts}次尝试后仍无法生成有效SQL")
            if check_result:
                st.error(f"最后一次错误: {check_result}")

        # 构建响应
        response = f"""
        ### SQL 查询
        ```sql
        {sql}
        ```
        
        ### 查询状态
        {'✅ 成功' if check_flag else '❌ 失败'}
        
        ### 查询结果
        ```
        {denotation}
        ```
        """

        st.success("成功执行SQL查询。")
        return response

    except Exception as e:
        st.error(f"执行SQL查询时发生错误: {e}")
        import traceback

        st.error(traceback.format_exc())  # 显示详细错误信息
        return f"查询出错: {e}"


# 界面显示
uploaded_tables = get_uploaded_tables()
if not uploaded_tables:
    st.warning(f"没有找到表格，请先上传表格文件。")
    st.stop()

selected_table = st.selectbox(
    "选择一个已上传的表格:",
    uploaded_tables,
    index=0,
    # help="选择您想要提问的文件。",
)

if selected_table:
    # st.info(f"您已选择表格: **{selected_table}**")

    # 从数据库中读取表格
    excel_sql_app = st.session_state.excel_sql_app
    db_engine = excel_sql_app.db_engine

    # 读取表格数据
    try:
        df = pd.read_sql_table(selected_table, db_engine)
        df = pd.read_sql(f"SELECT * FROM {selected_table}", db_engine)
        st.write(f"表格数据预览:")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"读取表格数据时发生错误: {e}")

    # try:
    #     df = pd.read_excel(selected_file_path)
    #     with st.expander("文件预览"):
    #         st.dataframe(df.head())
    # except Exception as e:
    #     st.warning(f"无法预览文件: {e}")

    # 输入问题
    user_question = st.text_area(
        "输入您的问题:",
        placeholder=f"例如：表格中有多少记录？",
        height=150,
        help="请详细描述您的问题。",
    )

    # 查询按钮
    if st.button("查询", disabled=not user_question):
        if not user_question:
            st.warning("请输入您的问题。")
        else:
            with st.spinner("正在查询中，请稍候..."):
                response = get_sql_response(user_question)

                st.subheader("🤖 查询结果:")
                st.markdown(response)
