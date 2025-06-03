from datetime import timedelta

from feast import FeatureView, Field
from feast.types import Float32

from fx_trader.feature_store.data_sources import news_sentiment_source
from fx_trader.feature_store.entities import currency_pair

# Assuming news_sentiment_source has 'event_timestamp', 'currency_pair_id',
# 'sentiment_score', 'relevance_score'.

news_sentiment_fv = FeatureView(
    name="news_sentiment_features",
    entities=[currency_pair],
    ttl=timedelta(hours=6),  # News sentiment can be relatively short-lived
    batch_source=news_sentiment_source,
    schema=[
        # Example: pre-aggregated
        Field(name="avg_sentiment_score_1h", dtype=Float32),
        # Example: pre-aggregated
        Field(name="max_relevance_score_1h", dtype=Float32),
    ],
    description="Aggregated news sentiment scores related to currency pairs.",
)
# Similar to technical features, aggregations like "avg_sentiment_score_1h" would typically
# be pre-calculated in the `news_sentiment.parquet` by an upstream job.
