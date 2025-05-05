from setuptools import setup, find_packages

setup(
    name="excellentsql",
    version="0.1.0",
    description="将Excel文件转换为SQL查询的工具",
    author="ycshao21",
    author_email="",
    packages=find_packages(),
    install_requires=[
        "openai",
        "mcp",
        "pandas",
        "python-dotenv",
        "colorama",
        "openpyxl",
        "hydra-core",
        "streamlit",
    ],
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.12",
    ],
)
