from datetime import timedelta
from pathlib import Path
from feast import Entity, FeatureView, Field, ValueType
from feast.types import Float32, Float64, Int64
from feast.infra.offline_stores.file_source import FileSource
from feast.infra.offline_stores.parquet import ParquetFileFormat

# データソースの定義
def define_data_sources(base_path: str):
    """特徴量のデータソースを定義する"""
    # 価格データソース
    price_source = FileSource(
        path=f"{base_path}/price_data.parquet",
        event_timestamp_column="timestamp",
        file_format=ParquetFileFormat(),
    )
    
    # マクロ経済データソース
    macro_source = FileSource(
        path=f"{base_path}/macro_data.parquet",
        event_timestamp_column="date",
        file_format=ParquetFileFormat(),
    )
    
    # ニュースデータソース
    news_source = FileSource(
        path=f"{base_path}/news_data.parquet",
        event_timestamp_column="publish_time",
        file_format=ParquetFileFormat(),
    )
    
    return price_source, macro_source, news_source

# エンティティの定義
def define_entities():
    """特徴量エンティティを定義する"""
    # 通貨ペアエンティティ
    currency_pair = Entity(
        name="currency_pair",
        value_type=ValueType.STRING,
        description="通貨ペア (例: USD_JPY, EUR_USD)",
    )
    
    # 経済指標エンティティ
    economic_indicator = Entity(
        name="economic_indicator",
        value_type=ValueType.STRING,
        description="経済指標の種類 (例: GDP, CPI, 失業率)",
    )
    
    return currency_pair, economic_indicator

# 特徴量ビューの定義
def define_feature_views(price_source, macro_source, news_source):
    """特徴量ビューを定義する"""
    # 価格特徴量
    price_features = FeatureView(
        name="price_features",
        entities=["currency_pair"],
        ttl=timedelta(days=365),
        schema=[
            Field(name="open", dtype=Float64),
            Field(name="high", dtype=Float64),
            Field(name="low", dtype=Float64),
            Field(name="close", dtype=Float64),
            Field(name="volume", dtype=Int64),
            Field(name="sma_20", dtype=Float64, description="20期間単純移動平均"),
            Field(name="sma_50", dtype=Float64, description="50期間単純移動平均"),
            Field(name="rsi_14", dtype=Float32, description="14期間RSI"),
            Field(name="macd", dtype=Float64, description="MACD"),
            Field(name="macd_signal", dtype=Float64, description="MACDシグナル"),
            Field(name="bollinger_upper", dtype=Float64, description="ボリンジャーバンド上限"),
            Field(name="bollinger_lower", dtype=Float64, description="ボリンジャーバンド下限"),
            Field(name="atr_14", dtype=Float64, description="14期間ATR"),
        ],
        online=True,
        source=price_source,
        tags={"category": "price"},
    )
    
    # マクロ経済特徴量
    macro_features = FeatureView(
        name="macro_features",
        entities=["economic_indicator"],
        ttl=timedelta(days=3650),  # 長期間保持
        schema=[
            Field(name="value", dtype=Float64, description="指標の値"),
            Field(name="change", dtype=Float64, description="前回比変化率"),
            Field(name="surprise", dtype=Float64, description="予想との差異"),
        ],
        online=True,
        source=macro_source,
        tags={"category": "macro"},
    )
    
    # ニュース特徴量
    news_features = FeatureView(
        name="news_features",
        entities=["currency_pair"],
        ttl=timedelta(days=30),
        schema=[
            Field(name="sentiment_score", dtype=Float32, description="感情スコア (-1.0〜1.0)"),
            Field(name="sentiment_magnitude", dtype=Float32, description="感情の強さ"),
            Field(name="relevance_score", dtype=Float32, description="関連性スコア"),
            Field(name="news_count", dtype=Int64, description="期間内のニュース件数"),
        ],
        online=True,
        source=news_source,
        tags={"category": "news"},
    )
    
    return price_features, macro_features, news_features

def create_feature_store_config(base_path: str = None):
    """特徴量ストアの設定を作成する"""
    if base_path is None:
        base_path = str(Path(__file__).parent / "data")
    
    # データソースの定義
    price_source, macro_source, news_source = define_data_sources(base_path)
    
    # エンティティの定義
    currency_pair, economic_indicator = define_entities()
    
    # 特徴量ビューの定義
    price_features, macro_features, news_features = define_feature_views(
        price_source, macro_source, news_source
    )
    
    # 特徴量ストアの設定を返す
    return {
        "entities": [currency_pair, economic_indicator],
        "feature_views": [price_features, macro_features, news_features],
        "data_sources": {
            "price": price_source,
            "macro": macro_source,
            "news": news_source,
        }
    }
