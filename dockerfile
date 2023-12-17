FROM python:3.11

RUN apt-get update

RUN pip install streamlit \
pandas \
st-gsheets-connection \
google-cloud-bigquery \
streamlit-extras \
altair

WORKDIR /app

COPY .streamlit/ /root/

EXPOSE 8501
