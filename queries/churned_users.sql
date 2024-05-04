WITH DateRanges AS (
  SELECT 
    DATE_SUB(date, INTERVAL 13 DAY) AS start_date_14,
    DATE_SUB(date, INTERVAL 27 DAY) AS start_date_28,
    date AS end_date,
    DENSE_RANK() OVER (ORDER BY date) AS active_week
  FROM 
    UNNEST(GENERATE_DATE_ARRAY('2023-11-26', '2024-05-12', INTERVAL 7 DAY)) AS date
),
PostThreadActiveUsers AS (
  SELECT DISTINCT
    SC.user_id,
    DR.active_week
  FROM 
    `geultto.geultto_9th.slack_conversation_master` SC
  JOIN
    DateRanges DR ON DATE(TIMESTAMP(SC.createtime)) BETWEEN DR.start_date_14 AND DR.end_date
  WHERE 
    SC.message_type IN ('post', 'thread')
),
SubmissionActiveUsers AS (
  SELECT DISTINCT
    REGEXP_EXTRACT(sc.text, r'<@(U[A-Z0-9]+)>') AS user_id,
    DR.active_week
  FROM 
    `geultto.geultto_9th.slack_conversation_master` SC
  JOIN
    DateRanges DR ON DATE(TIMESTAMP(SC.createtime)) BETWEEN DR.start_date_28 AND DR.end_date
  WHERE 
    REGEXP_CONTAINS(SC.text, r'gt;&gt;&gt;.*님 제출 완료.*')
),
EmojiActiveUsers AS (
  SELECT DISTINCT
    REPLACE(JSON_EXTRACT_SCALAR(user, '$'), '"', '') AS user_id,
    DR.active_week
  FROM 
    `geultto.geultto_9th.slack_conversation_master`,
    UNNEST(JSON_EXTRACT_ARRAY(reactions)) AS reaction,
    UNNEST(JSON_EXTRACT_ARRAY(JSON_EXTRACT(reaction, '$.user_id'))) AS user
  JOIN
    DateRanges DR ON DATE(TIMESTAMP(createtime)) BETWEEN DR.start_date_14 AND DR.end_date
  WHERE
    message_type IN ('post', 'thread')
),
ActiveUsers AS (
  SELECT 
    user_id,
    active_week
  FROM (
    SELECT user_id, active_week FROM PostThreadActiveUsers
    UNION DISTINCT
    SELECT user_id, active_week FROM SubmissionActiveUsers
    UNION DISTINCT
    SELECT user_id, active_week FROM EmojiActiveUsers
  )
),
AllUsers AS (
  SELECT 
    name,
    userid,
    department_slack
  FROM
    `geultto.geultto_9th.user_db_master`
),
PreviousWeek AS (
  SELECT 
    MAX(active_week) - 1 AS last_week
  FROM 
    DateRanges
),
InactiveUsers AS (
  SELECT
    AU.name,
    AU.userid,
    AU.department_slack
  FROM
    AllUsers AU
    CROSS JOIN PreviousWeek
    LEFT JOIN ActiveUsers AU2 ON AU.userid = AU2.user_id AND AU2.active_week = PreviousWeek.last_week
  WHERE
    AU2.user_id IS NULL
)
SELECT
  userid,
  name,
  department_slack
FROM 
  InactiveUsers
ORDER BY 
  userid;