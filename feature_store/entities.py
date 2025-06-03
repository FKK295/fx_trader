from feast import Entity, ValueType

# Entity for a currency pair, like EUR_USD
currency_pair = Entity(
    name="currency_pair",
    join_keys=["currency_pair_id"],  # The column name in your data source
    value_type=ValueType.STRING,
    description="A currency pair (e.g., EUR_USD, USD_JPY)",
)

# Entity for an event timestamp, typically when the data point was recorded
event_timestamp = Entity(
    name="event_timestamp",
    # No join_keys needed if it's implicitly the timestamp column in feature views
    value_type=ValueType.INT64,  # Assuming Unix timestamp for broader compatibility
    description="The timestamp of the event or observation",
)

# You could also define an entity for things like 'country' if you have country-specific macro data.
