CREATE TABLE IF NOT EXISTS historical_market_data
(
    offer_id VARCHAR(255) PRIMARY KEY
    , seniority VARCHAR(255)
    , date_added DATE
    , offer_name VARCHAR(255)
    , city VARCHAR(150)
    , company VARCHAR(255)
);