import argparse
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import mlflow
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from feast import FeatureStore
from sklearn.metrics import accuracy_score, f1_score, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split, TimeSeriesSplit

from fx_trader.config import settings
from fx_trader.config.trading_params import TradingParameters
from fx_trader.models.forecast import PriceForecaster  # Optional
from fx_trader.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def load_features_from_feast(
    fs: FeatureStore,
    entity_df: pd.DataFrame,
    feature_views_names: List[str],
    join_key: str = "currency_pair_id",
) -> pd.DataFrame:
    """
    Loads features from Feast for the given entities and feature views.
    """
    logger.info(
        f"Loading features for {len(entity_df)} entities from views: {feature_views_names}")

    # Ensure entity_df has the event_timestamp column required by Feast
    if "event_timestamp" not in entity_df.columns:
        # If not present, add a default timestamp (e.g., now). This might need adjustment
        # based on whether you're fetching historical point-in-time correct features.
        # For training, event_timestamp should correspond to the label's timestamp.
        logger.warning(
            "'event_timestamp' not in entity_df. Using current time. Ensure this is correct for training.")
        entity_df["event_timestamp"] = pd.Timestamp.utcnow()

    # Ensure join_key is in entity_df
    if join_key not in entity_df.columns:
        raise ValueError(
            f"Join key '{join_key}' not found in entity DataFrame.")

    # Construct feature services or directly use feature views
    # For simplicity, directly use feature view names if they are unique and accessible
    features_to_join = []
    for fv_name in feature_views_names:
        try:
            # This assumes feature view names are directly usable as feature references.
            # In more complex scenarios, you might need f"{fv_name}:feature_name"
            # or use FeatureServices.
            fv = fs.get_feature_view(fv_name)
            for feature in fv.features:
                features_to_join.append(f"{fv_name}:{feature.name}")
        except Exception as e:
            logger.error(f"Could not retrieve feature view {fv_name}: {e}")
            raise

    if not features_to_join:
        raise ValueError("No features selected to load from Feast.")

    logger.info(f"Requesting features: {features_to_join}")

    training_df = fs.get_historical_features(
        entity_df=entity_df,
        features=features_to_join,
        # full_feature_names=True # Set to True if you want fv_name__feature_name format
    ).to_df()

    logger.info(f"Successfully loaded features. Shape: {training_df.shape}")
    return training_df


def create_labels(df: pd.DataFrame, price_col: str = "close_price", horizon: int = 1, threshold: float = 0.0005) -> pd.DataFrame:
    """
    Creates binary classification labels (UP/DOWN) based on future price movement.
    Args:
        df: DataFrame with price data, must be sorted by time and grouped by currency_pair_id.
        price_col: The column containing the price to use for label generation.
        horizon: The number of periods in the future to look for price change.
        threshold: The minimum relative change for a significant move.
    Returns:
        DataFrame with a 'label' column (1 for UP, 0 for DOWN/STAY).
    """
    logger.info(
        f"Creating labels with horizon {horizon} and threshold {threshold}")
    df = df.copy()
    df['future_price'] = df.groupby('currency_pair_id')[
        price_col].shift(-horizon)
    df['price_change_pct'] = (
        df['future_price'] - df[price_col]) / df[price_col]

    df['label'] = 0  # Default to DOWN/STAY
    df.loc[df['price_change_pct'] > threshold, 'label'] = 1  # UP
    # df.loc[df['price_change_pct'] < -threshold, 'label'] = 0 # DOWN (already default)

    df.dropna(subset=['future_price', 'label'], inplace=True)
    logger.info(
        f"Labels created. Distribution: \n{df['label'].value_counts(normalize=True)}")
    return df


def train_xgboost_classifier(
    X_train: pd.DataFrame, y_train: pd.Series,
    X_val: pd.DataFrame, y_val: pd.Series,
    params: Dict[str, Any]
) -> xgb.XGBClassifier:
    """Trains an XGBoost classifier."""
    model = xgb.XGBClassifier(
        **params, use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train, eval_set=[
              (X_val, y_val)], early_stopping_rounds=10, verbose=False)
    return model


def objective(
    trial: optuna.Trial,
    X_train: pd.DataFrame, y_train: pd.Series,
    X_val: pd.DataFrame, y_val: pd.Series
) -> float:
    """Optuna objective function for hyperparameter tuning."""
    params = {
        "objective": "binary:logistic",
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=100),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "gamma": trial.suggest_float("gamma", 0, 5),
        "random_state": 42,
    }
    model = train_xgboost_classifier(X_train, y_train, X_val, y_val, params)
    preds_proba = model.predict_proba(X_val)[:, 1]
    logloss = log_loss(y_val, preds_proba)
    return logloss  # Optuna minimizes this


def run_training(
    feast_repo_path: str,
    feature_views: List[str],
    # Path to a parquet file defining entities and timestamps for training
    entity_source_path: str,
    label_horizon: int = 1,
    label_threshold: float = 0.0001,  # 1 basis point
    test_size: float = 0.2,
    n_optuna_trials: int = 20,
    experiment_name: str = "FX_Signal_Model",
    run_forecast_training: bool = False,
):
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        logger.info(
            f"Starting MLflow Run: {run_id} for Experiment: {experiment_name}")
        mlflow.log_params({
            "feast_repo_path": feast_repo_path,
            "feature_views": ", ".join(feature_views),
            "entity_source_path": entity_source_path,
            "label_horizon": label_horizon,
            "label_threshold": label_threshold,
            "test_size": test_size,
            "n_optuna_trials": n_optuna_trials,
            "run_forecast_training": run_forecast_training,
        })

        # 1. Load features from Feast
        fs = FeatureStore(repo_path=feast_repo_path)
        # Entity DataFrame should contain 'currency_pair_id' and 'event_timestamp'
        # 'event_timestamp' is crucial for point-in-time correctness.
        # This entity_df defines the "rows" for which we want to fetch features and generate labels.
        # Example: historical OHLCV data points for various pairs.
        # Expects columns: currency_pair_id, event_timestamp, close_price (for labels)
        entity_df = pd.read_parquet(entity_source_path)

        # Ensure event_timestamp is datetime
        entity_df['event_timestamp'] = pd.to_datetime(
            entity_df['event_timestamp'])

        # For training, we need features *before* the label's event_timestamp.
        # Feast handles this point-in-time join based on entity_df's timestamps.
        training_data = load_features_from_feast(fs, entity_df, feature_views)

        # 2. Create Labels
        # The 'close_price' for label creation should be from the original entity_df,
        # not a feature from Feast, to avoid data leakage if 'close_price' is also a feature.
        # Merge back the necessary price column if it's not already in training_data from entities.
        if 'close_price' not in training_data.columns and 'close_price' in entity_df.columns:
            training_data = pd.merge(training_data, entity_df[['currency_pair_id', 'event_timestamp', 'close_price']],
                                     on=['currency_pair_id', 'event_timestamp'], how='left')

        labeled_data = create_labels(
            training_data, price_col="close_price", horizon=label_horizon, threshold=label_threshold)

        # 3. Prepare data for XGBoost
        # Drop unnecessary columns (IDs, timestamps, raw price used for labels)
        features_to_drop = ['currency_pair_id', 'event_timestamp',
                            'future_price', 'price_change_pct', 'close_price']
        # Also drop any feature that was used to create the label if it's perfectly correlated or from the future.
        # This depends on your feature engineering.

        X = labeled_data.drop(columns=[
                              'label'] + [col for col in features_to_drop if col in labeled_data.columns])
        y = labeled_data['label']

        # Ensure all feature names are strings (XGBoost requirement)
        X.columns = [str(col) for col in X.columns]

        # Handle NaN values (e.g., fill with median or mean, or use XGBoost's NaN handling)
        X = X.fillna(X.median())  # Simple median imputation

        # Time-series split or standard split
        # For financial time series, TimeSeriesSplit is generally preferred.
        # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False) # Shuffle=False for time series
        tscv = TimeSeriesSplit(n_splits=5)  # Example: 5 splits
        # For simplicity in this example, using the last split from TSCV for train/val.
        # A more robust approach would be to iterate through splits or use a walk-forward validation.
        for train_index, val_index in tscv.split(X):
            X_train, X_val = X.iloc[train_index], X.iloc[val_index]
            y_train, y_val = y.iloc[train_index], y.iloc[val_index]

        logger.info(
            f"Training data shape: {X_train.shape}, Validation data shape: {X_val.shape}")

        # 4. Hyperparameter Tuning with Optuna
        study = optuna.create_study(direction="minimize")  # Minimize logloss
        study.optimize(lambda trial: objective(
            trial, X_train, y_train, X_val, y_val), n_trials=n_optuna_trials)

        best_params = study.best_params
        logger.info(f"Best Optuna parameters: {best_params}")
        mlflow.log_params({f"optuna_{k}": v for k, v in best_params.items()})
        mlflow.log_metric("best_optuna_logloss", study.best_value)

        # 5. Train final model with best params and log
        final_model = train_xgboost_classifier(
            X_train, y_train, X_val, y_val, best_params)

        val_preds_proba = final_model.predict_proba(X_val)[:, 1]
        val_preds = (val_preds_proba > 0.5).astype(int)  # Example threshold

        metrics = {
            "val_logloss": log_loss(y_val, val_preds_proba),
            "val_accuracy": accuracy_score(y_val, val_preds),
            "val_f1_score": f1_score(y_val, val_preds),
            "val_roc_auc": roc_auc_score(y_val, val_preds_proba),
        }
        logger.info(f"Validation Metrics: {metrics}")
        mlflow.log_metrics(metrics)

        mlflow.xgboost.log_model(final_model, "signal_xgboost_model")
        logger.info("XGBoost model training complete and logged to MLflow.")

        # (Optional) Train and log forecasting model
        if run_forecast_training:
            logger.info("Starting forecast model training...")
            # Assuming entity_df can be used for forecasting model training
            # This part needs to be adapted based on the PriceForecaster's requirements
            # forecaster = PriceForecaster()
            # forecaster.train(entity_df, target_column='close_price', date_column='event_timestamp')
            # forecast_eval_metrics = forecaster.evaluate(some_test_data) # Needs proper test data
            # mlflow.log_metrics({f"forecast_{k}": v for k, v in forecast_eval_metrics.items()})
            # mlflow.pyfunc.log_model(artifact_path="price_forecaster_model", python_model=forecaster) # If forecaster is a PyFunc model
            logger.warning(
                "Forecast model training part is a placeholder and needs implementation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FX Signal Model")
    parser.add_argument("--feast_repo", type=str,
                        default="feature_store", help="Path to Feast repository")
    parser.add_argument("--entity_source", type=str, required=True,
                        help="Path to Parquet file with entities for training (currency_pair_id, event_timestamp, close_price)")
    parser.add_argument("--horizon", type=int, default=4,
                        help="Labeling horizon (e.g., 4 for H1 means 4 hours ahead)")
    parser.add_argument("--threshold", type=float, default=0.0005,
                        help="Labeling threshold for price change (e.g. 0.0005 for 0.05%)")
    parser.add_argument("--optuna_trials", type=int,
                        default=10, help="Number of Optuna trials")
    parser.add_argument("--experiment", type=str,
                        default="FX_Signal_Model_XGBoost", help="MLflow experiment name")

    args = parser.parse_args()

    # Define which feature views to use for training
    # These names must match the 'name' attribute in your FeatureView definitions
    feature_view_names = [
        "price_technical_features",
        # "macro_economic_features", # Uncomment if macro features are ready and relevant
        # "news_sentiment_features", # Uncomment if news features are ready and relevant
    ]

    run_training(
        feast_repo_path=args.feast_repo,
        feature_views=feature_view_names,
        entity_source_path=args.entity_source,
        label_horizon=args.horizon,
        label_threshold=args.threshold,
        n_optuna_trials=args.optuna_trials,
        experiment_name=args.experiment,
    )
