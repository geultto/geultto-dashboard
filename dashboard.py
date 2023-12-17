import streamlit as st
import pandas as pd
import altair as alt
import helper
from datetime import timedelta, datetime, date
from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(page_title = "글또 대시보드",
        layout = "wide",
        initial_sidebar_state = "expanded" 
        )

st.title("글또 대시보드")

############## Side bar Start
# multiselect 높이 제한 css
st.markdown(
    """
    <style>
    div [data-baseweb=select]  {
        height: 400px;
        overflow: auto;
    }
    </style>
    """, unsafe_allow_html=True)

#날짜 필터링
start_date = st.sidebar.date_input("시작일", value=datetime(2021, 11, 19))
end_date = st.sidebar.date_input("끝", value=date.today())

#채널 필터링
ch_list = pd.DataFrame(helper.run_bigquery_query('channels.sql', st.secrets["gcp_service_account"]))

channels = list(ch_list['channel_name'].unique())
channels_container = st.sidebar.container()

# 전체 체크 상태, 데이터 초기화
if "all_option_channels" not in st.session_state:
    st.session_state.all_option_channels = True
    st.session_state.selected_options_channels = channels

def check_change(): # 필터링된 데이터 (selected_options_channels) 저장
    if st.session_state.all_option_channels:
        st.session_state.selected_options_channels = channels
    else:
        st.session_state.selected_options_channels = []
    return

def multi_change(): # 전체 선택 체크 상태(all_option_channels) 저장 
    if len(st.session_state.selected_options_channels) == len(channels):
        st.session_state.all_option_channels = True
    else:
        st.session_state.all_option_channels = False
    return

selected_channels = channels_container.multiselect('채널 선택', options = channels, default = channels, key="selected_options_channels", on_change=multi_change)
st.sidebar.checkbox("전체 선택", key='all_option_channels', on_change = check_change)

############## Side bar End

# 해당 기수 총 지표
col1, col2, col3, col4 = st.columns(4)
style_metric_cards(border_left_color = "#1E3D6B")

num_posts = pd.DataFrame(helper.run_bigquery_query('num_post.sql', st.secrets["gcp_service_account"]))
num_threads = pd.DataFrame(helper.run_bigquery_query('num_thread.sql', st.secrets["gcp_service_account"]))
total_emojis = pd.DataFrame(helper.run_bigquery_query('total_emojis.sql', st.secrets["gcp_service_account"]))

col1.metric("총 채널 수", len(ch_list)) 
col2.metric("총 post 수", num_posts['cnt'].sum()) 
col3.metric("총 thread 수", num_threads['cnt'].sum())
col4.metric("총 이모지 수", total_emojis['total_emoji_count'][0])

st.divider()

# 1. 포스트 수
# <@U065Z7248P9> 님이 채널에 참여함 .. 등의 포스트 제외 필요
filtered_posts = helper.filtering(
    dataframe=num_posts,
    start_date=start_date,
    end_date=end_date,
    channels=selected_channels
)

post_chart = alt.Chart( 
    filtered_posts
    ).mark_bar( 
        color='darkgreen',
        width = 15
    ).encode(
        x=alt.X('date:T', title=''),
        y=alt.Y('cnt:Q', title='post 수'),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=300
    ).interactive(bind_y = False)

# 2. 스레드 수

filtered_threads = helper.filtering(
    dataframe=num_threads,
    start_date=start_date,
    end_date=end_date,
    channels=selected_channels
)

thread_chart = alt.Chart( 
    filtered_threads
    ).mark_bar( 
        color='darkgreen',
        width = 15
    ).encode(
        x=alt.X('date:T', title=''),
        y=alt.Y('cnt:Q', title='thread 수'),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=300
    ).interactive(bind_y = False)

col1, col2 = st.columns(2)
col1.subheader("포스트 수")
col1.altair_chart(post_chart, use_container_width=True)
col2.subheader("스레드 수")
col2.altair_chart(thread_chart, use_container_width=True)

# 3. 패스 사용 수
# 날짜, 채널 필터링 x

deposit_sheet_conn = helper.connect_to_gsheet("gsheets2") # Deposit DB
deposit_df = deposit_sheet_conn.read(
    worksheet="현황",
    ttl="10m", # 10분마다 갱신
    usecols=list(range(6, 16)),
)

tmp = deposit_df.apply(lambda col: (col == 'pass').sum())
num_pass = pd.DataFrame({'마감일': tmp.index, 'pass수': tmp.values})
num_pass['마감일'] = num_pass['마감일'].apply(lambda x: x.split(' 오후')[0])
num_pass['마감일'] = pd.to_datetime(num_pass['마감일'], format='%Y. %m. %d')

pass_chart = alt.Chart( 
    num_pass
    ).mark_bar( 
        color='darkgreen',
        width = 15
    ).encode(
        x=alt.X('마감일:T', title=''),
        y=alt.Y('pass수:Q', title='패스 수'),
        tooltip=['마감일:T', 'pass수:Q']
    ).properties(
        height=300
    ).interactive(bind_y = False)

col1, col2 = st.columns(2)
col1.subheader("패스 수")
col1.altair_chart(pass_chart, use_container_width=True)




# 필터링 너무 느림.. 채널들 그룹화하기? (or 채널 필터링 필요 없을 수도)
# 보여줄 지표 고민
# 필터링 파트 helper.py 파일에 모듈화
# 로그인 기능 추가
