import streamlit as st

st.set_page_config(
    page_title="文档问答助手",
    page_icon="🤖",
    layout="wide"
)

st.title("欢迎使用EXCEL问答助手")

st.markdown("""
这是一个简单的 Web 应用，允许您上传EXCEL文档，然后基于该表格内容进行提问。

**如何使用:**

1.  **导航到 Upload File 页面:** 点击左侧边栏的 "Upload File"。
2.  **上传文件:** 上传Excel文件。文件内容会存储在当前会话中。
3.  **导航到 Ask Question 页面:** 点击左侧边栏的 "Ask Question"。
4.  **选择文件:** 从下拉列表中选择您之前上传的文件。
5.  **输入问题:** 在文本框中输入您想基于所选文档提出的问题。

""")

# 初始化 session state (如果还没有的话)
if 'uploaded_files_content' not in st.session_state:
    st.session_state.uploaded_files_content = {} # 字典：{filename: content}

st.sidebar.success("请在上方选择一个操作页面。")