WITH default_zero AS (
    SELECT DISTINCT
        0 AS offers_count
        , seniority
    FROM
        historical_market_data
)
, current_month AS (
    SELECT
        COUNT(*) AS offers_count
        , seniority
    FROM
        historical_market_data
    WHERE
        EXTRACT(MONTH FROM NOW()) = EXTRACT(MONTH FROM date_added)
    GROUP BY
        seniority
)


SELECT
    COALESCE(cm.offers_count, 0) AS offers_count
    , dz.seniority
FROM
    current_month cm
RIGHT JOIN
    default_zero dz ON dz.seniority = cm.seniority
ORDER BY
    dz.seniority
;