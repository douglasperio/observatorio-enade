@echo off
cd /d "%~dp0"
if not exist "dados\cpc.parquet" (
  echo Consolidando planilhas do INEP pela primeira vez...
  python etl\consolidar.py
)
start "" http://localhost:8501
python -m streamlit run app.py --server.port 8501
