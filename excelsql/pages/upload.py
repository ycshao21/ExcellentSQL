import streamlit as st
import os
import pandas as pd # 引入 pandas 用于处理 Excel

# 定义存储上传文件的目录
UPLOAD_DIR = "tmp"

# 确保上传目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

st.set_page_config(page_title="上传文件", page_icon="📤") # 设置页面配置

st.markdown("# 📤 上传 Excel 文件")
st.sidebar.header("上传文件") # 在侧边栏显示标题
st.write(
    """在此页面上传您的 Excel 文件。文件将被保存以供后续处理和聊天交互。"""
)

# --- 文件处理函数占位符 ---
def process_excel_file(file_path):
    """
    处理上传的 Excel 文件。
    您可以在这里添加具体的处理逻辑，例如：
    - 读取 Excel 数据
    - 数据清洗和转换
    - 特征提取
    - 将处理后的数据存储为特定格式 (如 CSV, Parquet) 或数据库
    Args:
        file_path (str): 上传文件的完整路径。

    Returns:
        bool: 处理是否成功。
        object: 处理结果 (可选)。
    """
    st.info(f"开始处理文件: {os.path.basename(file_path)}")
    try:
        # 示例：使用 pandas 读取 Excel 文件
        df = pd.read_excel(file_path)
        st.write("文件内容预览 (前 5 行):")
        st.dataframe(df.head())

        # ******************************************
        # 在下方添加您自己的文件处理逻辑
        # 例如： data_cleaning(df), feature_extraction(df)
        # processed_data = ...
        # save_processed_data(processed_data, ...)
        # ******************************************

        st.success(f"文件处理占位符函数已执行: {os.path.basename(file_path)}")
        # 返回 True 表示处理（占位符）成功
        return True, df # 示例返回 DataFrame
    except Exception as e:
        st.error(f"处理文件时出错 {os.path.basename(file_path)}: {e}")
        return False, None
# --- 文件处理函数占位符结束 ---


# Streamlit 文件上传组件
# accept_multiple_files=True 允许一次上传多个文件
uploaded_files = st.file_uploader(
    "请选择一个或多个 Excel 文件上传",
    type=['xlsx', 'xls'], # 限制文件类型为 Excel
    accept_multiple_files=True,
    help="支持 .xlsx 和 .xls 格式的文件。" # 添加帮助提示
)

if uploaded_files:
    st.write(f"共选择了 {len(uploaded_files)} 个文件。")
    saved_files_info = [] # 用于存储保存的文件信息

    for uploaded_file in uploaded_files:
        # 构建文件保存路径
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        # 检查文件是否已存在，避免重复处理 (可选)
        if os.path.exists(file_path):
            st.warning(f"文件 '{uploaded_file.name}' 已存在于 {UPLOAD_DIR} 目录中。将跳过上传和处理。")
            saved_files_info.append({"name": uploaded_file.name, "path": file_path, "status": "已存在"})
            continue # 跳过当前文件

        # 将上传的文件内容写入到服务器的文件中
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer()) # getbuffer() 获取文件内容

            st.success(f"文件 '{uploaded_file.name}' 已成功上传到: {file_path}")
            saved_files_info.append({"name": uploaded_file.name, "path": file_path, "status": "已上传"})

            # --- 调用文件处理函数 ---
            st.write(f"--- 开始处理文件: {uploaded_file.name} ---")
            success, result = process_excel_file(file_path)
            if success:
                st.write(f"--- 文件处理完成: {uploaded_file.name} ---")
                # 可选：在这里对 result 做些什么
            else:
                 st.write(f"--- 文件处理失败: {uploaded_file.name} ---")
            st.markdown("---") # 分隔符

        except Exception as e:
            st.error(f"保存文件 '{uploaded_file.name}' 时出错: {e}")
            saved_files_info.append({"name": uploaded_file.name, "path": file_path, "status": f"保存失败: {e}"})

    # 显示所有已处理（上传或跳过）的文件列表
    st.subheader("上传状态总结:")
    status_df = pd.DataFrame(saved_files_info)
    st.dataframe(status_df)

# 可以添加一个按钮来显示 tmp 文件夹中的文件列表
if st.button("查看已上传的文件列表"):
    try:
        files_in_tmp = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
        if files_in_tmp:
            st.write(f"`{UPLOAD_DIR}` 目录中的文件:")
            st.dataframe(files_in_tmp, column_config={"value": "文件名"}) # 显示为 DataFrame
        else:
            st.info(f"`{UPLOAD_DIR}` 目录当前为空。")
    except FileNotFoundError:
        st.error(f"目录 '{UPLOAD_DIR}' 不存在。请先上传文件。")
    except Exception as e:
        st.error(f"列出文件时出错: {e}")