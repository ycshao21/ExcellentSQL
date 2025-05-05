# ExcelSQL
```bash
git clone --recursive git@github.com:ycshao21/ExcelSQL.git

conda create -n excelsql python=3.12
pip install -e .
```

配置 `.env` 文件

将 Excel 文件放在 `data` 目录下，在 `config/main.yaml` 中指定 Excel 文件路径，然后运行 `python scripts/excelsql_demo.py`