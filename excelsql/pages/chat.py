# src/pages/2_Chat_with_File.py
import streamlit as st
import os
import openai 
from agents.sql_agent import SQLAgent

UPLOAD_DIR = "tmp"

st.set_page_config(page_title="与文件聊天", page_icon="💬") # 设置页面配置

st.markdown("# 💬 与文件聊天")
st.sidebar.header("与文件聊天") # 在侧边栏显示标题
st.write(
    """选择一个已上传的 Excel 文件，然后输入您的问题与 OpenAI 进行交互。"""
)

# --- Helper 函数：获取 tmp 目录下的 Excel 文件 ---
def get_uploaded_files(directory):
    """获取指定目录下的 Excel 文件列表"""
    files = []
    if os.path.exists(directory):
        try:
            files = [f for f in os.listdir(directory)
                     if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(('.xlsx', '.xls'))]
        except Exception as e:
            st.error(f"读取目录 '{directory}' 时出错: {e}")
    else:
        st.warning(f"目录 '{directory}' 不存在。请先在“上传文件”页面上传文件。")
    return files

# --- OpenAI 交互函数占位符 ---
def get_openai_response(selected_file_path, user_question, file_content_summary=None):

    st.info(f"正在向 OpenAI 发送问题，涉及文件: {os.path.basename(selected_file_path)}")
    st.info(f"用户问题: {user_question}")

    try:
        # --- 构建 Prompt ---
        # 这是一个简单的示例 prompt，您需要根据您的具体需求和
        # process_excel_file 函数的处理结果来构建更复杂的 prompt。
        prompt = f"""
        基于以下文件内容和用户问题，请提供回答。

        文件名: {os.path.basename(selected_file_path)}
        """
        # 如果有文件摘要信息，可以加入 prompt
        if file_content_summary:
             prompt += f"\n文件内容摘要:\n{file_content_summary}\n"

        prompt += f"""
        用户问题: {user_question}

        回答:
        """

        sql_agent = SQLAgent()

        answer = sql_agent.generate_sql(prompt)
        st.success("成功获取 OpenAI 回复。")
        return answer

    except openai.AuthenticationError:
         st.error("OpenAI API 密钥无效或过期，请检查配置。")
         return "OpenAI 认证失败。"
    except openai.RateLimitError:
        st.error("已达到 OpenAI API 请求速率限制，请稍后再试。")
        return "OpenAI 请求过于频繁。"
    except Exception as e:
        st.error(f"与 OpenAI 交互时发生错误: {e}")
        return f"与 OpenAI 交互时出错: {e}"

# --- Streamlit 界面 ---

# 1. 选择文件
uploaded_files = get_uploaded_files(UPLOAD_DIR)
if not uploaded_files:
    st.warning("`tmp` 目录中没有找到 Excel 文件。请先前往“上传文件”页面上传文件。")
    st.stop() # 如果没有文件，停止执行后续代码

selected_file = st.selectbox(
    "选择一个已上传的 Excel 文件:",
    uploaded_files,
    index=0, # 默认选择第一个文件
    help="选择您想要提问的文件。"
)

if selected_file:
    selected_file_path = os.path.join(UPLOAD_DIR, selected_file)
    st.info(f"您已选择文件: **{selected_file}**")

    # 可选：显示文件的一些基本信息或处理结果摘要
    # 这里可以调用 process_excel_file 或其变种来获取摘要
    # file_summary = get_summary_from_processed_file(selected_file_path)
    # if file_summary:
    #    st.expander("文件内容摘要").write(file_summary)

    # 2. 输入问题
    user_question = st.text_area(
        "输入您的问题:",
        placeholder=f"例如：总结一下 {selected_file} 文件中的主要内容？",
        height=150,
        help="请详细描述您的问题。"
    )

    # 3. 提交按钮和获取回复
    if st.button("向 OpenAI 提问", disabled=not user_question):
        if  not user_question:
            st.warning("请输入您的问题。")
        else:
            with st.spinner("正在思考中，请稍候..."):
                response = get_openai_response(selected_file_path, user_question)

                st.subheader("🤖 OpenAI 回复:")
                st.markdown(response) # 使用 markdown 显示回复，支持格式化
