WITH DateRanges AS (
  -- 기준 날짜로 설정된 9기 제출일
  SELECT 
    DATE_SUB(date, INTERVAL 14 DAY) AS start_date_14,
    DATE_SUB(date, INTERVAL 28 DAY) AS start_date_28,
    date AS submit_date
  FROM 
    UNNEST(GENERATE_DATE_ARRAY('2023-11-26', '2024-05-12', INTERVAL 14 DAY)) AS date
),
PostThreadActiveUsers AS (
  -- 2주 동안 적어도 하나의 post 또는 thread를 작성한 사용자 수
  SELECT DISTINCT
    SC.user_id,
    DR.submit_date
  FROM 
    `geultto.geultto_9th.slack_conversation_master` SC
  JOIN
    DateRanges DR ON DATE(TIMESTAMP(SC.createtime)) BETWEEN DR.start_date_14 AND DR.submit_date
  WHERE 
    SC.message_type IN ('post', 'thread')
),
SubmissionActiveUsers AS (
  -- 4주 동안 적어도 한 번 글을 제출한 사용자 수
  SELECT DISTINCT
    REGEXP_EXTRACT(sc.text, r'<@(U[A-Z0-9]+)>') AS user_id,
    DR.submit_date
  FROM 
    `geultto.geultto_9th.slack_conversation_master` SC
  JOIN
    DateRanges DR ON DATE(TIMESTAMP(SC.createtime)) BETWEEN DR.start_date_28 AND DR.submit_date
  WHERE 
    REGEXP_CONTAINS(SC.text, r'gt;&gt;&gt;.*님 제출 완료.*')
),
EmojiActiveUsers AS (
  -- 지난 2주 동안의 포스트나 쓰레드에 적어도 한 개의 이모지를 클릭한 사용자 수
  SELECT DISTINCT
    REPLACE(JSON_EXTRACT_SCALAR(user, '$'), '"', '') AS user_id,
    DR.submit_date
  FROM 
    `geultto.geultto_9th.slack_conversation_master`,
    UNNEST(JSON_EXTRACT_ARRAY(reactions)) AS reaction,
    UNNEST(JSON_EXTRACT_ARRAY(JSON_EXTRACT(reaction, '$.user_id'))) AS user
  JOIN
    DateRanges DR ON DATE(TIMESTAMP(createtime)) BETWEEN DR.start_date_14 AND DR.submit_date
  WHERE
    message_type IN ('post', 'thread')
),
ActiveUsers AS (
  -- 활성 유저: 셋 중 적어도 하나에 해당하는 유저
  SELECT 
    user_id,
    submit_date
  FROM (
    SELECT user_id, submit_date FROM PostThreadActiveUsers
    UNION DISTINCT
    SELECT user_id, submit_date FROM SubmissionActiveUsers
    UNION DISTINCT
    SELECT user_id, submit_date FROM EmojiActiveUsers
  )
),
AllUsersCount AS (
  -- 전체 유저 수
  SELECT 
    COUNT(*) AS total_users
  FROM
    `geultto.geultto_9th.users`
)
SELECT
  DR.submit_date AS date,
  COUNT(DISTINCT AU.user_id) AS active_users_count,
  COUNT(DISTINCT AU.user_id) / MAX(AUC.total_users) AS user_activity_ratio -- 활성 유저 비율
FROM 
  DateRanges DR
LEFT JOIN 
  ActiveUsers AU ON DR.submit_date = AU.submit_date
CROSS JOIN 
  AllUsersCount AUC
GROUP BY 
  DR.submit_date
ORDER BY 
  DR.submit_date;


-- WITH DateRange AS (
--   SELECT DATE('2023-11-19') + INTERVAL x DAY as date
--   FROM UNNEST(GENERATE_ARRAY(0, DATE_DIFF(CURRENT_DATE(), DATE('2023-11-19'), DAY))) AS x
-- ), ActiveUsers AS (
--   SELECT 
--     DATE(TIMESTAMP(createtime)) AS date,
--     COUNT(DISTINCT user_id) AS active_users_count
--   FROM (
--     SELECT 
--       user_id, 
--       createtime
--     FROM `geultto.geultto_9th.slack_conversation_master`
--     WHERE DATE(TIMESTAMP(createtime)) BETWEEN '2023-11-19' AND CURRENT_DATE()
--       AND message_type IN ('post', 'thread')
--   ) 
--   GROUP BY date
-- ), TotalUsers AS (
--   SELECT COUNT(DISTINCT userid) AS total_users
--   FROM `geultto.geultto_9th.user_db_master`
-- )
-- SELECT 
--   DateRange.date,
--   COALESCE(ActiveUsers.active_users_count, 0) AS active_users_count,
--   COALESCE(ActiveUsers.active_users_count, 0) / TotalUsers.total_users AS user_activity_ratio
-- FROM DateRange
-- LEFT JOIN ActiveUsers ON DateRange.date = ActiveUsers.date, TotalUsers
-- ORDER BY DateRange.date