SELECT
    COUNT(*) AS offers_count
    , seniority
FROM
    historical_market_data
WHERE
    EXTRACT(MONTH FROM NOW()) = EXTRACT(MONTH FROM date_added)
GROUP BY
    seniority
;
