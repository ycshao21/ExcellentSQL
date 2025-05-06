import sys
import os
# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import yaml
from omegaconf import OmegaConf
from dotenv import load_dotenv

from excelsql.excelsql import ExcelSQL

# 直接读取配置文件，不使用hydra
def init_excel_sql():
    try:
        # 加载环境变量
        load_dotenv()
        
        # 从config文件夹中读取main.yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'main.yaml')
        with open(config_path, 'r') as file:
            config_dict = yaml.safe_load(file)
        
        # 转换为OmegaConf对象
        cfg = OmegaConf.create(config_dict)
        
        # 初始化ExcelSQL实例
        app = ExcelSQL(cfg)
        return app
    except Exception as e:
        st.error(f"初始化ExcelSQL失败: {e}")
        return None

# 在会话状态中保存ExcelSQL实例
if 'excel_sql_app' not in st.session_state:
    st.session_state.excel_sql_app = init_excel_sql()
    
    # 如果初始化失败，显示错误信息
    if st.session_state.excel_sql_app is None:
        st.error("ExcelSQL初始化失败，请检查配置和环境设置")

# 设置页面配置
st.set_page_config(
    page_title="EXCEL问答助手",
    page_icon="🤖",
    layout="wide"
)

st.title("欢迎使用EXCEL问答助手")

st.markdown("""
这是一个简单的 Web 应用，允许您上传EXCEL文档，然后基于该表格内容进行提问。

**如何使用:**

1.  **导航到 Upload File 页面:** 点击左侧边栏的 "Upload File"。
2.  **上传文件:** 上传Excel文件。文件内容会导入数据库并存储在当前会话中。
3.  **导航到 Ask Question 页面:** 点击左侧边栏的 "Ask Question"。
4.  **选择文件:** 从下拉列表中选择您之前上传的文件。
5.  **输入问题:** 在文本框中输入您想基于所选文档提出的问题。

""")

# 初始化 session state (如果还没有的话)
if 'uploaded_files_content' not in st.session_state:
    st.session_state.uploaded_files_content = {} # 字典：{filename: content}

# 确保 data 目录存在，用于存储上传的文件
os.makedirs("data", exist_ok=True)

# 添加一个状态指示器，帮助调试
if st.session_state.excel_sql_app is not None:
    st.sidebar.success("ExcelSQL实例已成功初始化")
else:
    st.sidebar.error("ExcelSQL实例初始化失败")

st.sidebar.success("请在上方选择一个操作页面。")

# 这是Streamlit应用的入口点
if __name__ == "__main__":
    pass  # Streamlit会自动执行上面的代码