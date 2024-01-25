import streamlit as st
import pandas as pd
import altair as alt
import helper
from datetime import timedelta, datetime, date
from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(page_title="글또 운영대시보드",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )

############## Side bar start ##############

# multiselect 높이 제한 CSS
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

ch_list = pd.DataFrame(helper.run_bigquery_query(
    'channels.sql', st.secrets["gcp_service_account"]))
channels = list(ch_list['channel_name'].unique())

if "selected_options_channels" not in st.session_state:
    st.session_state.selected_options_channels = channels

col1, col2 = st.sidebar.columns([1, 1])
all_selected = col2.checkbox("전체 채널 선택", value=True, key='all_option_channels')

if all_selected:
    st.session_state.selected_options_channels = channels
else:
    if st.session_state.selected_options_channels == channels:
        st.session_state.selected_options_channels = []

with st.sidebar.form(key='channel_form'):
    channels_container = st.container()
    selected_channels = channels_container.multiselect(
        '채널 선택', options=channels, default=st.session_state.selected_options_channels, key="selected_options_channels")
    col1, col2 = st.columns([3, 1])
    with col2:
        submit_button = st.form_submit_button(label='적용')

# 현재 전체 채널 체크 후 일부 채널을 지워도 다시 전체채널이 선택되는 문제 있음, 하나라도 빠지면 전체 채널 선택 체크 해제되게 해야하는데,
# st.form이 애초에 변경값을 임시저장했다가 한 번에 보내기 위한 기능이고,  콜백함수를 받지 못하는 점 떄문에 막혀있음.
# 현재는 일부채널만 보기 위해서는 전체선택 체크 해제 후 원하는 채널을 전부 선택해야함.

############## Side bar End ##############

if submit_button:

    # Load data
    num_posts = pd.DataFrame(helper.run_bigquery_query(
        'num_post.sql', st.secrets["gcp_service_account"]))
    num_threads = pd.DataFrame(helper.run_bigquery_query(
        'num_thread.sql', st.secrets["gcp_service_account"]))
    total_emojis = pd.DataFrame(helper.run_bigquery_query(
        'total_emojis.sql', st.secrets["gcp_service_account"]))

    deposit_sheet_conn = helper.connect_to_gsheet("gsheets2")  # Deposit DB

    deposit_df = deposit_sheet_conn.read(
        worksheet="현황",
        ttl="10m",
        usecols=list(range(6, 16)),
    )

    # Dashboard Contents

    # 1. 해당 기수 총 지표
    col1, col2, col3, col4 = st.columns(4)
    style_metric_cards(border_left_color="#1E3D6B")

    col1.metric("총 채널 수", f"{len(ch_list):,}개")
    col2.metric("총 게시글 수", f"{num_posts['cnt'].sum():,}개")
    col3.metric("총 댓글 수", f"{num_threads['cnt'].sum():,}개")
    col4.metric("총 이모지 수", f"{total_emojis['total_emoji_count'][0]:,}개")

    # 2. 제출, 미제출, 패스
    col1, col2 = st.columns(2)

    submit_counts = deposit_df.apply(lambda col: (col == 0).sum())
    not_submit_counts = deposit_df.apply(lambda col: (col == -10000).sum())
    pass_counts = deposit_df.apply(lambda col: (col == 'pass').sum())
    summary_df = pd.DataFrame(
        {'제출': submit_counts, '미제출': not_submit_counts, '패스': pass_counts})

    summary_df.index = summary_df.index.to_series().apply(
        lambda x: x.replace('오후', 'PM'))
    summary_df.index = pd.to_datetime(
        summary_df.index, format='%Y. %m. %d %p %H:%M:%S').date

    submission_df = summary_df.reset_index().melt(
        'index', var_name='제출여부', value_name='수')

    color_scale = alt.Scale(scheme='greens')

    stacked_bar_chart = alt.Chart(submission_df).mark_bar(
        width=20
    ).encode(
        x=alt.X('index:T', title=''),
        y=alt.Y('수:Q', scale=alt.Scale(domain=[0, 450]), title='', stack='zero'),
        color=alt.Color('제출여부:N', scale=color_scale, legend=None),
        tooltip=['index:T', '제출여부:N', '수:Q']
    ).properties(
        height=400,
        title='날짜별 제출, 미제출, 패스 수'
    )

    col1.altair_chart(stacked_bar_chart, use_container_width=True)

    # 3. 포스트, 스레드 수 추이
    # 포스트
    # <@U065Z7248P9> 님이 채널에 참여함 .. 등의 포스트는 제외 필요
    filtered_posts = helper.filtering(
        dataframe=num_posts,
        start_date=start_date,
        end_date=end_date,
        channels=selected_channels
    )

    aggregated_data = filtered_posts.groupby('date')['cnt'].sum().reset_index()

    post_chart = alt.Chart(
        aggregated_data
    ).mark_area( 
        line={'color':'darkgreen'},
        interpolate='basis',
        color=alt.Gradient(
            gradient='linear',
            stops=[
                alt.GradientStop(color='white', offset=0),
                alt.GradientStop(color='darkgreen', offset=1)
                ],
            x1=1,
            x2=1,
            y1=1,
            y2=0
            )
    ).encode(
        x=alt.X('date:T', title=''),
        y=alt.Y('cnt:Q', title=''),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=344
    ).interactive(bind_y=False)

    # 스레드

    filtered_threads = helper.filtering(
        dataframe=num_threads,
        start_date=start_date,
        end_date=end_date,
        channels=selected_channels
    )
    aggregated_data = filtered_threads.groupby(
        'date')['cnt'].sum().reset_index()

    thread_chart = alt.Chart(
        aggregated_data
    ).mark_area( 
        line={'color':'darkgreen'},
        interpolate='basis',
        color=alt.Gradient(
            gradient='linear',
            stops=[
                alt.GradientStop(color='white', offset=0),
                alt.GradientStop(color='darkgreen', offset=1)
                ],
            x1=1,
            x2=1,
            y1=1,
            y2=0
            )
    ).encode(
        x=alt.X('date:T', title=''),
        y=alt.Y('cnt:Q', title=''),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=344
    ).interactive(bind_y=False)
    with col2:
        tab1, tab2 = st.tabs(["포스트 추이", "댓글 추이"])
        tab1.altair_chart(post_chart, use_container_width=True)
        tab2.altair_chart(thread_chart, use_container_width=True)

    # 3. 대숲
    col1, col2, col3 = st.columns([1,1,1])

    aggregated_data = num_posts[num_posts.channel_name == '1_대나무숲_고민_공유']

    bamboo_chart = alt.Chart(
        aggregated_data
    ).mark_area( 
        line={'color':'darkgreen'},
        interpolate='basis',
        color=alt.Gradient(
            gradient='linear',
            stops=[
                alt.GradientStop(color='white', offset=0),
                alt.GradientStop(color='darkgreen', offset=1)
                ],
            x1=1,
            x2=1,
            y1=1,
            y2=0
            )
    ).encode(
        x=alt.X('date:T', title=''),
        y=alt.Y('cnt:Q', title=''),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=300,  title='대숲 추이'
    ).interactive(bind_y=False)

    with col1:
        bamboo_chart

    # 4. 커피챗
    aggregated_data = num_posts[num_posts.channel_name == '1_커피챗_모임_후기']

    coffee_chart = alt.Chart(
        aggregated_data
    ).mark_area( 
        line={'color':'darkgreen'},
        interpolate='basis',
        color=alt.Gradient(
            gradient='linear',
            stops=[
                alt.GradientStop(color='white', offset=0),
                alt.GradientStop(color='darkgreen', offset=1)
                ],
            x1=1,
            x2=1,
            y1=1,
            y2=0
            )
    ).encode(
        x=alt.X('date:T', title=''),
        y=alt.Y('cnt:Q', title=''),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=300, title='커피챗 인증 추이'
    ).interactive(bind_y=False)

    with col2:
        coffee_chart

    # 5. 최근 2주 동안 가장 활발했던 소모임 채널 top 10
    gathering_set = set([s for s in num_posts.channel_name if s.startswith("4_")])
    num_posts['date'] = pd.to_datetime(num_posts['date'])
    two_weeks_ago = datetime.now() - timedelta(weeks=2)
    filtered_df = num_posts[num_posts['date'] >= two_weeks_ago]
    grouped_df = filtered_df.groupby('channel_name')['cnt'].sum().reset_index()
    top_10_channels = grouped_df[grouped_df.channel_name.isin(gathering_set)].sort_values(by='cnt', ascending=False).head(10)

    color_scale = alt.Scale(scheme='greens')
    chart_top10 = ( 
        alt.Chart()
        .mark_bar()
        .encode(
            x=alt.X("cnt:Q", title=""),
            y=alt.Y("channel_name:N", title="").sort('-x'),
            color=alt.Color("cnt:Q", scale=color_scale, legend=None),
        )
        .properties(height=215, title='최근 2주 간 소모임 Top 10')
    )

    top_ch_chart = alt.vconcat(chart_top10, data=top_10_channels, title="")
    col3.altair_chart(top_ch_chart, theme="streamlit", use_container_width=True)



# future work
# 필터링 파트 helper.py 파일에 모듈화
# 로그인 기능 추가 (private 하게만 공개하면 로그인 기능 필요없을수도?)
# 전체 현황 / 개인 현황 페이지 나누기
# 개인 현황 페이지에는 네트워크 그린다음에 클릭하면 아이디 보고 검색하면 개인정보 볼 수 있게 하고, 활동 저조한 분 표시하기?
