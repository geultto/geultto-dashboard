import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
from streamlit_gsheets import GSheetsConnection
import streamlit as st

# SQL 파일 로드
def load_sql(filename):
    with open(filename, 'r') as file:
        return file.read()

# BigQuery 연결 및 쿼리 실행
def run_bigquery_query(sql_file, credentials_info):
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info)
    client = bigquery.Client(credentials=credentials)
    query = load_sql(f'queries/{sql_file}')
    query_job = client.query(query)
    rows_raw = query_job.result()
    return [dict(row) for row in rows_raw]

# Google Sheets 연결
def connect_to_gsheet(connection_name):
    return st.connection(connection_name, type=GSheetsConnection)

# 날짜 필터링 함수
def filtering(dataframe, start_date=None, end_date=None):
    if start_date is None or end_date is None:
        raise ValueError("start date, end date 확인필요")

    dataframe['date'] = pd.to_datetime(dataframe['date']).dt.date
    filtered_df = dataframe[
        (dataframe['date'] >= start_date) &
        (dataframe['date'] <= end_date)
    ]
    return filtered_df
