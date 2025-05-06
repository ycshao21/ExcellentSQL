# src/pages/2_Chat_with_File.py
import streamlit as st
import os
import pandas as pd
import sys
# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 上传文件存储的目录
UPLOAD_DIR = "data"

# 设置页面配置
st.set_page_config(page_title="与文件聊天", page_icon="💬")

# 检查ExcelSQL实例是否已初始化
if 'excel_sql_app' not in st.session_state or st.session_state.excel_sql_app is None:
    st.error("ExcelSQL应用未初始化，请返回主页重新启动应用")
    st.stop()

st.markdown("# 💬 与文件聊天")
st.sidebar.header("与文件聊天")
st.write(
    """选择一个已上传的 Excel 文件，然后输入您的问题。"""
)

# 获取上传文件列表
def get_uploaded_files(directory):
    """获取指定目录下的Excel文件列表"""
    files = []
    if os.path.exists(directory):
        try:
            files = [f for f in os.listdir(directory)
                     if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(('.xlsx', '.xls'))]
        except Exception as e:
            st.error(f"读取目录 '{directory}' 时出错: {e}")
    else:
        st.warning(f"目录 '{directory}' 不存在。请先在上传文件页面上传文件。")
    return files

# SQL查询处理函数
def get_sql_response(selected_file_path, user_question):
    st.info(f"正在处理问题，涉及文件: {os.path.basename(selected_file_path)}")
    st.info(f"用户问题: {user_question}")

    try:
        # 获取共享的ExcelSQL实例
        excel_sql_app = st.session_state.excel_sql_app
        
        # 标准化查询
        normalized_query = excel_sql_app.normalize_query(user_question)
        st.write(f"标准化后的查询: {normalized_query}")
        
        # 生成SQL并执行
        results = excel_sql_app.generate_sqls_and_check(
            query=normalized_query,
            concurrent=True,
        )
        
        # 获取最终SQL和结果
        sql, flag, denotation = excel_sql_app.poll_sqls(results)
        
        # 构建响应
        response = f"""
        ### SQL 查询
        ```sql
        {sql}
        ```
        
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
uploaded_files = get_uploaded_files(UPLOAD_DIR)
if not uploaded_files:
    st.warning(f"`{UPLOAD_DIR}` 目录中没有找到Excel文件，请先上传文件。")
    st.stop()

selected_file = st.selectbox(
    "选择一个已上传的Excel文件:",
    uploaded_files,
    index=0,
    help="选择您想要提问的文件。"
)

if selected_file:
    selected_file_path = os.path.join(UPLOAD_DIR, selected_file)
    st.info(f"您已选择文件: **{selected_file}**")
    
    # 显示文件预览
    try:
        df = pd.read_excel(selected_file_path)
        with st.expander("文件预览"):
            st.dataframe(df.head())
    except Exception as e:
        st.warning(f"无法预览文件: {e}")

    # 输入问题
    user_question = st.text_area(
        "输入您的问题:",
        placeholder=f"例如：表格中有多少记录？",
        height=150,
        help="请详细描述您的问题。"
    )

    # 查询按钮
    if st.button("查询", disabled=not user_question):
        if not user_question:
            st.warning("请输入您的问题。")
        else:
            with st.spinner("正在查询中，请稍候..."):
                response = get_sql_response(selected_file_path, user_question)
                
                st.subheader("🤖 查询结果:")
                st.markdown(response)
