WITH LastSubmissionActivity AS (
  SELECT
    REGEXP_EXTRACT(text, r'<@(U[A-Z0-9]+)>') AS user_id,
    MAX(tddate) AS last_activity_date
  FROM
    `geultto.geultto_9th.slack_conversation_master`
  WHERE
    REGEXP_CONTAINS(text, r'gt;&gt;&gt;.*님 (제출 완료|패스 완료).*')
  GROUP BY
    user_id
  HAVING
    MAX(tddate) <= DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY)
),
LastPostThreadActivity AS(
  SELECT 
    user_id, 
    MAX(tddate) AS last_activity_date
  FROM 
    `geultto.geultto_9th.slack_conversation_master`
  WHERE 
    DATE(TIMESTAMP(createtime)) BETWEEN '2023-11-19' AND CURRENT_DATE()
    AND message_type IN ('post', 'thread')
  GROUP BY
    user_id
  HAVING
    MAX(tddate) <= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
),
CombinedActivity AS (
  SELECT 
    user_id, 
    '4주 동안 글 제출하지 않음' AS type, 
    last_activity_date
  FROM 
    LastSubmissionActivity
  
  UNION ALL
  
  SELECT 
    user_id, 
    '2주 동안 post, thread를 달지 않음' AS type, 
    last_activity_date
  FROM 
    LastPostThreadActivity
)

SELECT
  ca.user_id AS userid,
  udb.name,
  udb.department_slack,
  ca.type,
  ca.last_activity_date
FROM
  CombinedActivity ca
JOIN
  `geultto.geultto_9th.user_db_master` udb
ON
  ca.user_id = udb.userid
ORDER BY name ASC;