import streamlit as st
import os
import pandas as pd
import sys
# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 定义存储上传文件的目录
UPLOAD_DIR = "data"

# 确保上传目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

st.set_page_config(page_title="上传文件", page_icon="📤")

# 检查ExcelSQL实例是否已初始化
if 'excel_sql_app' not in st.session_state or st.session_state.excel_sql_app is None:
    st.error("ExcelSQL应用未初始化，请返回主页重新启动应用")
    st.stop()

st.markdown("# 📤 上传 Excel 文件")
st.sidebar.header("上传文件")
st.write(
    """在此页面上传您的 Excel 文件。文件将被导入到数据库并保存以供后续处理和聊天交互。"""
)

def process_excel_file(file_path):
    """处理上传的Excel文件并导入到数据库"""
    st.info(f"开始处理文件: {os.path.basename(file_path)}")
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        st.write("文件内容预览 (前 5 行):")
        st.dataframe(df.head())

        # 使用共享的ExcelSQL实例导入数据
        excel_sql_app = st.session_state.excel_sql_app
        success = excel_sql_app.upload_excel(file_path)
        
        if success:
            st.success(f"文件 {os.path.basename(file_path)} 已成功导入到数据库")
            return True, df
        else:
            st.error(f"导入文件 {os.path.basename(file_path)} 到数据库失败")
            return False, df
            
    except Exception as e:
        st.error(f"处理文件时出错 {os.path.basename(file_path)}: {e}")
        import traceback
        st.error(traceback.format_exc())  # 显示详细错误信息
        return False, None

# 文件上传组件
uploaded_files = st.file_uploader(
    "请选择一个或多个 Excel 文件上传",
    type=['xlsx', 'xls'],
    accept_multiple_files=True,
    help="支持 .xlsx 和 .xls 格式的文件。"
)

if uploaded_files:
    st.write(f"共选择了 {len(uploaded_files)} 个文件。")
    saved_files_info = []

    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        if os.path.exists(file_path):
            st.warning(f"文件 '{uploaded_file.name}' 已存在于 {UPLOAD_DIR} 目录中。将跳过上传和处理。")
            saved_files_info.append({"name": uploaded_file.name, "path": file_path, "status": "已存在"})
            continue

        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"文件 '{uploaded_file.name}' 已成功上传到: {file_path}")
            saved_files_info.append({"name": uploaded_file.name, "path": file_path, "status": "已上传"})

            st.write(f"--- 开始处理文件: {uploaded_file.name} ---")
            success, result = process_excel_file(file_path)
            if success:
                st.write(f"--- 文件处理完成: {uploaded_file.name} ---")
            else:
                st.write(f"--- 文件处理失败: {uploaded_file.name} ---")
            st.markdown("---")

        except Exception as e:
            st.error(f"保存文件 '{uploaded_file.name}' 时出错: {e}")
            saved_files_info.append({"name": uploaded_file.name, "path": file_path, "status": f"保存失败: {e}"})

    st.subheader("上传状态总结:")
    status_df = pd.DataFrame(saved_files_info)
    st.dataframe(status_df)

if st.button("查看已上传的文件列表"):
    try:
        files_in_data = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
        if files_in_data:
            st.write(f"`{UPLOAD_DIR}` 目录中的文件:")
            st.dataframe(files_in_data, column_config={"value": "文件名"})
        else:
            st.info(f"`{UPLOAD_DIR}` 目录当前为空。")
    except FileNotFoundError:
        st.error(f"目录 '{UPLOAD_DIR}' 不存在。请先上传文件。")
    except Exception as e:
        st.error(f"列出文件时出错: {e}")