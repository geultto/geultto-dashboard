import streamlit as st
import pandas as pd
import altair as alt
import helper
from datetime import timedelta, datetime, date
from streamlit_extras.metric_cards import style_metric_cards
from st_aggrid import AgGrid

def display_dashboard(name):

    style_metric_cards(border_left_color="#1E3D6B")

    ############## Side bar start ##############

    start_date = st.sidebar.date_input("시작일", value=datetime(2023, 11, 19))
    end_date = st.sidebar.date_input("종료일", value=date.today())

    ############## Side bar End ##############

    ############## 데이터 로드##############
        
    # 포스트 수, 스레드 수, 이모지 수
    num_posts = pd.DataFrame(helper.run_bigquery_query(
        'num_post.sql', st.secrets["gcp_service_account"]))
    num_threads = pd.DataFrame(helper.run_bigquery_query(
        'num_thread.sql', st.secrets["gcp_service_account"]))
    num_emojis = pd.DataFrame(helper.run_bigquery_query(
        'num_emojis.sql', st.secrets["gcp_service_account"]))

    # 글 제출 집계 (from deposit DB)
    deposit_sheet_conn = helper.connect_to_gsheet("gsheets2")

    deposit_df = deposit_sheet_conn.read(
        worksheet="현황",
        ttl="10m",
        usecols=list(range(8, 19)), #현재 수동으로 바꾸는 중
    )

    submit_counts = deposit_df.apply(lambda col: (col == 0).sum())
    not_submit_counts = deposit_df.apply(lambda col: (col == -10000).sum())
    pass_counts = deposit_df.apply(lambda col: (col == 'pass').sum())

    summary_df = pd.DataFrame({'제출': submit_counts, '미제출': not_submit_counts, '패스': pass_counts})
    summary_df.index = summary_df.index.to_series().apply(lambda x: x.replace('오후', 'PM'))

    summary_df.index = pd.to_datetime(summary_df.index, format='%Y. %m. %d %p %H:%M:%S').date


    # 유저 활성도
    active_user_df = pd.DataFrame(helper.run_bigquery_query('active_users_num.sql', st.secrets["gcp_service_account"]))

    # 채널 활성도
    active_channel_df = pd.DataFrame(helper.run_bigquery_query('active_channels.sql', st.secrets["gcp_service_account"]))

    # 제출 여부
    submit_df = pd.DataFrame(helper.run_bigquery_query('submit.sql', st.secrets["gcp_service_account"]))

    aggregated_results = []
    DUE_DATES = [  # 글또 시작일 을 포함한 오름차순 마감일 리스트
        datetime(2023, 11, 26).date(),  # 0회차 - 시작일
        datetime(2023, 12, 10).date(),  # 1회차
        datetime(2023, 12, 24).date(),  # 2회차
        datetime(2024, 1, 7).date(),  # 3회차
        datetime(2024, 1, 21).date(),  # 4회차
        datetime(2024, 2, 4).date(),  # 5회차
        datetime(2024, 2, 18).date(),  # 6회차
        datetime(2024, 3, 3).date(),  # 7회차
        datetime(2024, 3, 17).date(),  # 8회차
        datetime(2024, 3, 31).date(),  # 9회차
        datetime(2024, 4, 14).date(),  # 10회차
        datetime(2024, 4, 28).date(),  # 11회차
        datetime(2024, 5, 12).date(),  # 12회차 - 종료일
    ]

    # 각 회차 마감일의 13일 전부터 마감일까지 제출한 글 수 
    for due_date in DUE_DATES:
        count_start_date = due_date - timedelta(days=13) 
        mask = (submit_df['date'].dt.date >= count_start_date) & (submit_df['date'].dt.date <= due_date)
        filtered_df = submit_df.loc[mask]
        total_submits = filtered_df['submit'].sum()
        aggregated_results.append((due_date, total_submits))

    aggregated_df = pd.DataFrame(aggregated_results, columns=['due_date', 'total_submits'])

    # 다음 due date
    current_date = pd.Timestamp.today().date()
    next_due_date_row = aggregated_df[aggregated_df['due_date'] >= current_date].head(1)

    # 리텐션 테이블을 위한 데이터프레임
    active_users_list_df = pd.DataFrame(helper.run_bigquery_query(
    'active_users.sql', st.secrets["gcp_service_account"]))

    churned_df = pd.DataFrame(helper.run_bigquery_query(
        'churned_users.sql', st.secrets["gcp_service_account"]))

    ############## 데이터 로드끝 ##############

    # 1. 어제의 글또 활성화 정도
    col1, col2, col3= st.columns(3)

    col1.metric("어제의 활성 유저 수 (%)", 
                f"{active_user_df.iloc[-2]['active_users_count']}명 ({active_user_df.iloc[-2]['user_activity_ratio'] * 100:.1f}%)", 
                f"{(active_user_df.iloc[-2]['user_activity_ratio'] - active_user_df.iloc[-3]['user_activity_ratio']) * 100:.1f}%"
                )
    col2.metric("어제의 활성 채널 수 (%)",
                f"{active_channel_df.iloc[-2]['active_channels_count']}개 ({active_channel_df.iloc[-2]['channel_activity_ratio'] * 100:.1f}%)",
                f"{(active_channel_df.iloc[-2]['channel_activity_ratio'] - active_channel_df.iloc[-3]['channel_activity_ratio']) * 100:.1f}%"
                )
    col3.metric(f"이번 회차 글 제출 수 (다음 마감일: {next_due_date_row.iloc[0]['due_date']})",
                f"{next_due_date_row.iloc[0]['total_submits']}개",   
                f"어제 {submit_df.iloc[-2]['submit']}개의 글이 새로 제출되었습니다"
                )

    # 2. 유저 활성 관련 지표 추세
    col1, col2 = st.columns(2)

    ## 2-1. 활성 유저 수, 글 제출 수, 포스트 수, 댓글 수, 이모지 수  추이 차트

    ### 유저 활성도 (포스트 + 댓글  + 제출 + 이모지 종합)

    filtered_active_user_df = helper.filtering(
        dataframe=active_user_df,
        start_date=start_date,
        end_date=end_date,
    )

    active_user_chart = alt.Chart(
        filtered_active_user_df
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
        y=alt.Y('active_users_count:Q', title=''),
        tooltip=['date:T', 'active_users_count:Q']
    ).properties(
        height=344
    ).interactive(bind_y=False)

    ### 글 제출 수

    filtered_submit_df= helper.filtering(
        dataframe=submit_df,
        start_date=start_date,
        end_date=end_date,
    )

    submit_chart = alt.Chart(
        filtered_submit_df
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
        y=alt.Y('submit:Q', title=''),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=344
    ).interactive(bind_y=False)
    
    ### 포스트 수
    # <@U065Z7248P9> 님이 채널에 참여함 .. 등의 포스트는 제외 필요
    filtered_posts = helper.filtering(
        dataframe=num_posts,
        start_date=start_date,
        end_date=end_date,
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

    ### 스레드 수

    filtered_threads = helper.filtering(
        dataframe=num_threads,
        start_date=start_date,
        end_date=end_date,
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

    ### 이모지 수 (이모지가 달린 포스트의 createtime으로 계산하기 때문에 정확한 정확한 날짜는 아님)

    filtered_emojis = helper.filtering(
        dataframe=num_emojis,
        start_date=start_date,
        end_date=end_date,
    )
    aggregated_data = filtered_emojis.groupby(
        'date')['cnt'].sum().reset_index()

    emoji_chart = alt.Chart(
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

    with col1:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["활성 유저 수", "글 제출 수", "포스트 수", "댓글 수", "이모지 수"])
        tab1.altair_chart(active_user_chart, use_container_width=True)
        tab2.altair_chart(submit_chart, use_container_width=True)
        tab3.altair_chart(post_chart, use_container_width=True)
        tab4.altair_chart(thread_chart, use_container_width=True)
        tab5.altair_chart(emoji_chart, use_container_width=True)

    ## 2-2. 회차 별 제출, 미제출, 패스 수 추이
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
        title='회차 별 제출, 미제출, 패스 수'
    )

    col2.altair_chart(stacked_bar_chart, use_container_width=True)

    # 3. 채널 활성 관련 지표 추세
    
    ## 3-1. 채널 활성화 추이
    
    col1, col2, col3 = st.columns(3)

    active_channel_chart = alt.Chart(
        active_channel_df
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
        y=alt.Y('active_channels_count:Q', title=''),
        tooltip=['date:T', 'cnt:Q']
    ).properties(
        height=360,  title='채널 활성화 추이'
    ).interactive(bind_y=False)

    col1.altair_chart(active_channel_chart, theme="streamlit", use_container_width=True)

    ## 3-2. 대숲 추이

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
        height=300
    ).interactive(bind_y=False)

    ## 3-3. 커피챗 추이
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
        height=300
    ).interactive(bind_y=False)

    with col2:
        tab1, tab2 = st.tabs(["커피챗 인증 추이", "대숲 추이"])
        tab1.altair_chart(coffee_chart, use_container_width=True)
        tab2.altair_chart(bamboo_chart, use_container_width=True)
        
    ## 3-4. 소모임 Top 10
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
            y=alt.Y("channel_name:N", title="Channels", sort=alt.EncodingSortField(field="cnt", order="descending")),
            color=alt.Color("cnt:Q", scale=color_scale, legend=None),
        )
        .properties(height=268, title='최근 2주 간 소모임 Top 10')
    )

    top_ch_chart = alt.vconcat(chart_top10, data=top_10_channels, title="")
    col3.altair_chart(top_ch_chart, theme="streamlit", use_container_width=True)

    # 4. 이탈 유저 관련 지표
    # 비활성 유저 정의: 2번(4주) 연속 글 제출 x or 14일 동안 댓글, 포스트 x, 14일 동안 이모지 x
    col1, col2 = st.columns([0.7, 1.3])

    ## 4-1. 지난 주 비활성 유저  리스트
    grid_options = {
        "columnDefs": [
            {
                "headerName": "id",
                "field": "userid",
                "width": 150
            },
            {
                "headerName": "이름",
                "field": "name", 
                "width": 100
            },
            {
                "headerName": "체널",
                "field": "department_slack", 
                "width": 270
            },
        ],
}
    
    with col1:
        st.markdown("##### 지난 주 이탈 유저 리스트")
        AgGrid(churned_df, 
            gridOptions = grid_options,
            height = 350,
            theme = 'alpine',
            custom_css = { 
                "#gridToolBar": {
                    "padding-bottom": "0px !important"
                    } 
                }
            )

    ## 4-2. 리텐션 테이블
    weeks = active_users_list_df['active_week'].unique().tolist()
    weeks.sort() 

    user_weeks = pd.pivot_table(active_users_list_df, values='active_week', index='user_id', columns='active_week', aggfunc=lambda x: 1, fill_value=0)
    retention_matrix = pd.DataFrame(index=weeks, columns=weeks, data=0)

    for i in range(len(weeks)-1):
        for j in range(i+1, len(weeks)):
            prev_week = user_weeks[weeks[i]]
            curr_week = user_weeks[weeks[j]]
            retention_matrix.at[weeks[i], weeks[j]] = ((prev_week & curr_week) == 1).sum() / prev_week.sum()

    retention_long = retention_matrix.reset_index().melt(id_vars='index', var_name='week', value_name='retention')
    retention_long['retention'] = retention_long['retention'].round(3) * 100

    # 초록색 계열로 커스텀 컬러 매핑을 정의
    color_scale = alt.Scale(domain=[0, 70, 100],
                            range=["#F5FBEF", "#E6F8E0", "#21610B"])


    chart = alt.Chart(retention_long).mark_rect().encode(
        x=alt.X('week:O', title='주차'),
        y=alt.Y('index:O', title='주차'),
        color=alt.Color('retention:Q', scale=color_scale, legend=alt.Legend(title="리텐션 비율")),
        tooltip=['week', 'retention']
    ).properties(
        width=400,
        height=400,
    )

    with col2:
        st.markdown("##### 리텐션 테이블 (단위: %)")
        st.altair_chart(chart, use_container_width=True)

if __name__ == '__main__':
    display_dashboard()