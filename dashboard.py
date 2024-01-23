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

############## Side bar Start ##############
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

start_date = st.sidebar.date_input("시작일", value=datetime(2023, 11, 19))
end_date = st.sidebar.date_input("종료일", value=date.today())

ch_list = pd.DataFrame(helper.run_bigquery_query('channels.sql', st.secrets["gcp_service_account"]))
channels = list(ch_list['channel_name'].unique())

if "selected_options_channels" not in st.session_state:
    st.session_state.selected_options_channels = channels

col1, col2 = st.sidebar.columns([1,1]) 
all_selected = col2.checkbox("전체 채널 선택", value=True, key='all_option_channels')

if all_selected:
    st.session_state.selected_options_channels = channels
else:
    if st.session_state.selected_options_channels == channels:
        st.session_state.selected_options_channels = []

with st.sidebar.form(key='channel_form'):
    channels_container = st.container()
    selected_channels = channels_container.multiselect('채널 선택', options=channels, default=st.session_state.selected_options_channels, key="selected_options_channels")
    col1, col2 = st.columns([3,1]) 
    with col2:
        submit_button = st.form_submit_button(label='적용')

############## Side bar End ##############
if submit_button:
    # 해당 기수 총 지표
    col1, col2, col3, col4 = st.columns(4)
    style_metric_cards(border_left_color = "#1E3D6B")

    num_posts = pd.DataFrame(helper.run_bigquery_query('num_post.sql', st.secrets["gcp_service_account"]))
    num_threads = pd.DataFrame(helper.run_bigquery_query('num_thread.sql', st.secrets["gcp_service_account"]))
    total_emojis = pd.DataFrame(helper.run_bigquery_query('total_emojis.sql', st.secrets["gcp_service_account"]))

    col1.metric("총 채널 수", f"{len(ch_list):,}개") 
    col2.metric("총 게시글 수", f"{num_posts['cnt'].sum():,}개") 
    col3.metric("총 댓글 수", f"{num_threads['cnt'].sum():,}개")
    col4.metric("총 이모지 수", f"{total_emojis['total_emoji_count'][0]:,}개")

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




# future work
# 필터링 너무 느림.. 채널들 그룹화하기? (or 필터링 한 후 버튼 눌러야 적용되도록)
# 보여주는 지표 개선
# 필터링 파트 helper.py 파일에 모듈화
# 로그인 기능 추가 (private 하게만 공개하면 로그인 기능 필요없을수도?)
# 전체 현황 / 개인 현황 페이지 나누기
# 개인 현황 페이지에는 네트워크 그린다음에 클릭하면 아이디 보고 검색하면 개인정보 볼 수 있게 하고, 활동 저조한 분 표시하기?
