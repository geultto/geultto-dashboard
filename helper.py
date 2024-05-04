import pandas as pd
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from google.cloud import bigquery
from streamlit_gsheets import GSheetsConnection
import streamlit as st

# SQL 파일 로드
def load_sql(filename: str) -> str:
    with open(filename, 'r') as file:
        return file.read()

# BigQuery 연결 및 쿼리 실행
@st.cache_data(ttl=43200)  # 12시간 간격
def run_bigquery_query(sql_file: str, _credentials_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    credentials = service_account.Credentials.from_service_account_info(_credentials_info)
    client = bigquery.Client(credentials=credentials)
    query = load_sql(f'queries/{sql_file}')
    query_job = client.query(query)
    rows_raw = query_job.result()
    return [dict(row) for row in rows_raw]

# Google Sheets 연결
def connect_to_gsheet(connection_name: str) -> GSheetsConnection:
    return st.connection(connection_name, type=GSheetsConnection)

# 날짜 필터링 함수
def filtering(dataframe: pd.DataFrame, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    if start_date is None or end_date is None:
        raise ValueError("start date, end date 확인필요")

    dataframe['date'] = pd.to_datetime(dataframe['date']).dt.date
    filtered_df = dataframe[
        (dataframe['date'] >= start_date) &
        (dataframe['date'] <= end_date)
    ]
    return filtered_df
