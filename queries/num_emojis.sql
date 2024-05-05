SELECT
    DATE(createtime) as date,
    COUNT(*) as cnt
FROM (
    SELECT
        REPLACE(user_id, '"', '') as user_id,
        createtime
    FROM `geultto.geultto_9th.slack_conversation_master`,
    UNNEST(JSON_EXTRACT_ARRAY(reactions)) as reaction,
    UNNEST(JSON_EXTRACT_ARRAY(JSON_EXTRACT(reaction, '$.user_id'))) as user_id
) SC
JOIN `geultto.geultto_9th.users` U ON SC.user_id = U.user_id
GROUP BY DATE(createtime)
ORDER BY date ASC