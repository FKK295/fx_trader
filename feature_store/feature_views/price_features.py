from datetime import timedelta

import pandas as pd
import talib
from feast import FeatureView, Field
from feast.types import Float32, Int64

from data_sources import price_data_source
from entities import currency_pair


# Define a UDF for TA-Lib calculations if not using PandasTransformations directly
# For simple TA-Lib functions, PandasTransformations are often cleaner.
# However, if you need more complex logic or multiple outputs from one pass, a UDF can be useful.

# Using @batch_feature_view or FeatureView with PandasTransformation

price_technical_fv = FeatureView(
    name="price_technical_features",
    entities=[currency_pair],
    ttl=timedelta(hours=2),  # How long features live in the online store
    batch_source=price_data_source,
    # online=True, # Default is True
    schema=[
        Field(name="sma_10", dtype=Float32),
        Field(name="sma_30", dtype=Float32),
        Field(name="ema_10", dtype=Float32),
        Field(name="ema_30", dtype=Float32),
        Field(name="rsi_14", dtype=Float32),
        Field(name="macd_signal", dtype=Float32),  # MACD signal line
        Field(name="macd_hist", dtype=Float32),  # MACD histogram
        Field(name="bbands_upper", dtype=Float32),
        Field(name="bbands_middle", dtype=Float32),
        Field(name="bbands_lower", dtype=Float32),
        Field(name="atr_14", dtype=Float32),
        # Pass through close for convenience
        Field(name="close_price", dtype=Float32),
        Field(name="volume_val", dtype=Int64),   # Pass through volume
    ],
    description="Technical indicators derived from OHLCV price data.",
    # To use UDFs for transformation:
    # from feast import udf
    # @udf(output_dtypes=[Float32, Float32, ...])
    # def calculate_ta_features(df: pd.DataFrame) -> pd.DataFrame: ...
    # batch_source=price_data_source.with_transformation(transformation=calculate_ta_features)
)

# If you prefer to define transformations directly within the FeatureView (more common for Feast)
# you would typically use a RequestSource for on-demand features or a StreamSource for stream processing.
# For batch transformations on a FileSource, you often precompute them or use a BatchFeatureView
# with a transformation function.

# Let's refine this to use a transformation logic that Feast can apply during materialization.
# This usually involves creating a BatchFeatureView or using a transformation on the source.
# For simplicity with FileSource and batch features, often features are pre-calculated and stored,
# or a more advanced setup with Spark/Pandas UDFs is used.

# A common pattern for TA-Lib with Feast on Pandas is to define a transformation function
# that will be applied to the DataFrame loaded from the batch_source.
# This requires a bit more setup, often involving a custom FeatureView class or a specific
# way to register the transformation if not using `PandasTransformation` directly in newer Feast versions.

# For now, let's assume these features would be computed by a separate process that updates
# the Parquet files, or that you'd use a more advanced Feast transformation mechanism.

# A simplified way to represent this for now, assuming features are pre-calculated in the source Parquet:
# If features are ALREADY in price_data.parquet:
# price_technical_fv_precomputed = FeatureView(
#     name="price_technical_features_precomputed",
#     entities=[currency_pair],
#     ttl=timedelta(hours=2),
#     batch_source=price_data_source, # Assuming price_data_source now contains these columns
#     schema=[
#         Field(name="sma_10", dtype=Float32),
#         Field(name="rsi_14", dtype=Float32),
#         # ... other precomputed features
#     ]
# )

# To actually compute them with Feast using Pandas, you'd typically use a `PythonTransformation`
# (or `PandasTransformation` in older Feast versions) if available for `FileSource`,
# or more commonly, features are pre-materialized by an external job, or you use an `OnDemandFeatureView`
# if they can be computed from other already materialized features or request data.

# Let's assume for this example that we will define a UDF and attach it,
# or that a future step in an orchestration pipeline would compute these.
# For a "production-grade" system, these features would often be computed and stored
# as part of the ETL that prepares `price_data.parquet`, or using Feast's stream/batch processing capabilities
# with appropriate transformations.

# For the purpose of this generation, we'll define the FeatureView schema.
# The actual computation logic would be part of the materialization process or an upstream job.
# If using `feast apply`, Feast expects the source data to conform or transformations to be defined.

# To make this runnable with `feast materialize` and have TA-Lib calculations,
# you would typically use a `feast.transformation.PandasTransformation` (if your Feast version supports it well with FileSource)
# or structure it as an `OnDemandFeatureView` if inputs are other features, or precompute.

# For now, this FeatureView declares the *intent* to have these features.
# The materialization step would need to ensure they are computed.
# A common approach is to have an ETL job that reads raw OHLCV, computes TA features,
# and writes to the `price_data_source` Parquet file. Feast then just reads these.

# If you want Feast to do the computation from a simpler base OHLCV source,
# you would use an `OnDemandFeatureView` (if inputs are other FVs or request data)
# or a more complex setup for batch transformations.

# Let's assume `price_data_source` contains ONLY ohlcv and timestamp, and we want to define
# how to compute these. This is where `OnDemandFeatureView` or a transformation step is key.
# However, `OnDemandFeatureView` is typically for features derived from *other features* or *request data*,
# not directly from a raw batch source with complex transformations like TA-Lib.

# The most straightforward way with Feast for batch sources like Parquet is that the
# Parquet file *already contains* these computed features.
# The `batch_source` then just points to this enriched Parquet file.
# The ETL/transformation logic (using Pandas, TA-Lib) happens *before* Feast's materialization,
# preparing the data for Feast.

# So, the `price_data.parquet` that `price_data_source` points to should ideally already have these columns.
# The definition above then simply tells Feast about them.
