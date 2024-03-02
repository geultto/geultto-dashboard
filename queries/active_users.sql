WITH DateRange AS (
  SELECT DATE('2023-11-19') + INTERVAL x DAY as date
  FROM UNNEST(GENERATE_ARRAY(0, DATE_DIFF(CURRENT_DATE(), DATE('2023-11-19'), DAY))) AS x
), ActiveUsers AS (
  SELECT 
    DATE(TIMESTAMP(createtime)) AS date,
    COUNT(DISTINCT user_id) AS active_users_count
  FROM (
    SELECT 
      user_id, 
      createtime
    FROM `geultto.geultto_9th.slack_conversation_master`
    WHERE DATE(TIMESTAMP(createtime)) BETWEEN '2023-11-19' AND CURRENT_DATE()
      AND message_type IN ('post', 'thread')
  ) 
  GROUP BY date
), TotalUsers AS (
  SELECT COUNT(DISTINCT userid) AS total_users
  FROM `geultto.geultto_9th.user_db_master`
)
SELECT 
  DateRange.date,
  COALESCE(ActiveUsers.active_users_count, 0) AS active_users_count,
  COALESCE(ActiveUsers.active_users_count, 0) / TotalUsers.total_users AS user_activity_ratio
FROM DateRange
LEFT JOIN ActiveUsers ON DateRange.date = ActiveUsers.date, TotalUsers
ORDER BY DateRange.date


-- -- 이모지까지 합산할 일이 있을까싶어 일단 남겨둠
-- WITH ActiveUsers1dayBefore AS (
--     SELECT DISTINCT user_id
--     FROM `geultto.geultto_9th.slack_conversation_master`
--     --WHERE DATE(createtime) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
--     WHERE DATE(TIMESTAMP(createtime)) = '2024-02-18'
--     AND (message_type IN ('post', 'thread'))
--     UNION DISTINCT
--     SELECT DISTINCT reaction_user_id AS user_id
--     FROM `geultto.geultto_9th.slack_conversation_master`,
--     UNNEST(JSON_EXTRACT_ARRAY(reactions)) AS sep_by_reactions,
--     UNNEST(JSON_EXTRACT_ARRAY(JSON_EXTRACT(sep_by_reactions, '$.user_id'))) AS reaction_user_id
--     --WHERE DATE(createtime) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
--     WHERE DATE(TIMESTAMP(createtime)) = '2024-02-18'
-- ), ActiveUsers2dayBefore AS (
--     SELECT DISTINCT user_id
--     FROM `geultto.geultto_9th.slack_conversation_master`
--     --WHERE DATE(createtime) = DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
--     WHERE DATE(TIMESTAMP(createtime)) = '2024-02-17'
--     AND (message_type IN ('post', 'thread'))
--     UNION DISTINCT
--     SELECT DISTINCT reaction_user_id AS user_id
--     FROM `geultto.geultto_9th.slack_conversation_master`,
--     UNNEST(JSON_EXTRACT_ARRAY(reactions)) AS sep_by_reactions,
--     UNNEST(JSON_EXTRACT_ARRAY(JSON_EXTRACT(sep_by_reactions, '$.user_id'))) AS reaction_user_id
--     --WHERE DATE(createtime) = DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
--     WHERE DATE(TIMESTAMP(createtime)) = '2024-02-17'
-- ),TotalUsers AS (
--     SELECT COUNT(DISTINCT userid) AS total_users
--     FROM `geultto.geultto_9th.user_db_master`
-- ), ActiveUsers1dayBeforeCount AS (
--     SELECT COUNT(*) AS active_users
--     FROM ActiveUsers1dayBefore
-- ), ActiveUsers2dayBeforeCount AS (
--     SELECT COUNT(*) AS active_users
--     FROM ActiveUsers2dayBefore
-- )
-- SELECT
--     ActiveUsers1dayBeforeCount.active_users / TotalUsers.total_users AS user_activity_ratio_1day_before,
--     ActiveUsers2dayBeforeCount.active_users / TotalUsers.total_users AS user_activity_ratio_2day_before
-- FROM ActiveUsers1dayBeforeCount, ActiveUsers2dayBeforeCount, TotalUsers;