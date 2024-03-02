WITH DateRange AS (
  SELECT DATE('2023-11-19') + INTERVAL x DAY as date
  FROM UNNEST(GENERATE_ARRAY(0, DATE_DIFF(CURRENT_DATE(), DATE('2023-11-19'), DAY))) AS x
), ActiveChannels AS (
  SELECT 
    DATE(TIMESTAMP(createtime)) AS date, 
    COUNT(DISTINCT channel_id) AS active_channels_count
  FROM `geultto.geultto_9th.slack_conversation_master`
  WHERE DATE(TIMESTAMP(createtime)) BETWEEN '2023-11-19' AND CURRENT_DATE()
    AND message_type IN ('post', 'thread')
  GROUP BY date
), TotalChannels AS (
  SELECT COUNT(DISTINCT channel_id) AS total_channels
  FROM `geultto.geultto_9th.channels`
)
SELECT 
  DateRange.date,
  COALESCE(ActiveChannels.active_channels_count, 0) AS active_channels_count,
  COALESCE(ActiveChannels.active_channels_count, 0) / TotalChannels.total_channels AS channel_activity_ratio
FROM DateRange
LEFT JOIN ActiveChannels ON DateRange.date = ActiveChannels.date, TotalChannels
ORDER BY DateRange.date