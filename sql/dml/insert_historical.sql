INSERT INTO historical_market_data
(
    offer_id
    , seniority
    , date_added
    , offer_name
    , city
    , company
)
VALUES 
{values}
ON CONFLICT (offer_id) DO NOTHING;