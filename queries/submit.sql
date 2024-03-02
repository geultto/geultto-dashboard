WITH DateRange AS (
  SELECT DATE('2023-11-19') + INTERVAL x DAY as date
  FROM UNNEST(GENERATE_ARRAY(0, DATE_DIFF(CURRENT_DATE(), DATE('2023-11-19'), DAY))) AS x
), AggregatedCounts AS (
  SELECT
    DATE(TIMESTAMP(createtime)) AS date,
    COUNTIF(REGEXP_CONTAINS(text, r'gt;&gt;&gt.*님 제출 완료.*')) AS submit,
    COUNTIF(REGEXP_CONTAINS(text, r'gt;&gt;&gt.*님 패스 완료.*')) AS pass
  FROM `geultto.geultto_9th.slack_conversation_master`
  WHERE
    DATE(TIMESTAMP(createtime)) BETWEEN '2023-11-19' AND CURRENT_DATE()
  GROUP BY
    date
)
SELECT
  dr.date,
  IFNULL(ac.submit, 0) AS submit,
  IFNULL(ac.pass, 0) AS pass
FROM
  DateRange dr
LEFT JOIN
  AggregatedCounts ac ON dr.date = ac.date
ORDER BY
  dr.date;