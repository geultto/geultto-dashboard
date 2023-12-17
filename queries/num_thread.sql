-- 날짜 별, 채널 별 thread 수 세기
SELECT
    ch.channel_name,
    DATE(mt.createtime) AS date,
    COUNT(*) AS cnt
FROM
    `geultto.geultto_9th.slack_conversation_master` mt
JOIN
    `geultto.geultto_9th.channels` ch ON mt.channel_id = ch.channel_id
WHERE
    mt.message_type = 'thread'
GROUP BY
    date, ch.channel_name
ORDER BY
    date, ch.channel_name