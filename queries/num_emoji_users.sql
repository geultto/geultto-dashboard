-- 지난 2주 동안의 포스트나 쓰레드에 적어도 한 개의 이모지를 클릭한 사용자 수 (EmojiActiveUsers)
WITH DateRanges AS (
  SELECT 
    DATE_SUB(date, INTERVAL 14 DAY) AS start_date_14,
    date AS submit_date
  FROM 
    UNNEST(GENERATE_DATE_ARRAY('2023-11-26', '2024-05-12', INTERVAL 14 DAY)) AS date
),
EmojiActiveUsers AS (
  SELECT DISTINCT
    REPLACE(JSON_EXTRACT_SCALAR(user, '$'), '"', '') AS user_id,
    dr.submit_date
  FROM 
    `geultto.geultto_9th.slack_conversation_master`,
    UNNEST(JSON_EXTRACT_ARRAY(reactions)) AS reaction,
    UNNEST(JSON_EXTRACT_ARRAY(JSON_EXTRACT(reaction, '$.user_id'))) AS user
  JOIN
    DateRanges dr ON DATE(TIMESTAMP(createtime)) BETWEEN dr.start_date_14 AND dr.submit_date
  WHERE
    message_type IN ('post', 'thread')
)

SELECT 
  dr.date,
  COUNT(eau.user_id) AS cnt
FROM 
  DateRanges dr
LEFT JOIN 
  EmojiActiveUsers eau ON dr.submit_date = eau.submit_date
GROUP BY 
  dr.submit_date
ORDER BY 
  dr.submit_date;