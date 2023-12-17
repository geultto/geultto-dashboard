-- 총 이모지 세기
SELECT
    COUNT(*) as total_emoji_count
FROM (
SELECT
    REPLACE(user_id, '"', '') as user_id
    FROM `geultto.geultto_9th.slack_conversation_master`,
    UNNEST(JSON_EXTRACT_ARRAY(reactions)) as reaction,
    UNNEST(JSON_EXTRACT_ARRAY(JSON_EXTRACT(reaction, '$.user_id'))) as user_id
    ) r
JOIN `geultto.geultto_9th.users` u ON r.user_id = u.user_id