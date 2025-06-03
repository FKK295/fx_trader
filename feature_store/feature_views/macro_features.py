from datetime import timedelta

from feast import FeatureView, Field
from feast.types import Float32, String

from fx_trader.feature_store.data_sources import macro_data_source
# Or a new 'country' entity
from fx_trader.feature_store.entities import currency_pair

# Assuming macro_data_source has 'event_timestamp', 'currency_pair_id' (mapped from country),
# 'indicator_name', 'value'.
# You might need an intermediate step to map country-specific data to currency pairs.

macro_economic_fv = FeatureView(
    name="macro_economic_features",
    # Or a country entity if data is country-specific
    entities=[currency_pair],
    ttl=timedelta(days=30),  # Macro data changes less frequently
    batch_source=macro_data_source,
    schema=[
        # e.g., "CPI_YoY", "InterestRate"
        Field(name="indicator_name", dtype=String),
        Field(name="indicator_value", dtype=Float32),
    ],
    description="Macro-economic indicators like CPI and interest rates, potentially mapped to currency pairs.",
)

# Note: Mapping country-specific data (e.g., US CPI, EU CPI) to a currency_pair entity
# (e.g., EUR_USD) would require transformation logic or careful data preparation in the
# `macro_data.parquet` file to include a `currency_pair_id` column.
