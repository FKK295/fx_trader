import argparse
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import mlflow
import pandas as pd
from evidently.pipeline.column_mapping import ColumnMapping
from evidently.report import Report
from evidently.metrics import (
    ColumnDriftMetric,
    DatasetDriftMetric,
    DataDriftTable,
    RegressionPerformanceMetrics,  # If regression model
    ClassificationPerformanceMetrics,  # If classification model
)
from feast import FeatureStore

from fx_trader.config import settings
from fx_trader.mlops.train import run_training  # To trigger retraining
from fx_trader.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def check_drift_and_performance(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    column_mapping: ColumnMapping,
    model_type: str = "classification",  # "classification" or "regression"
) -> Tuple[bool, Dict[str, Any]]:
    """
    Checks for data drift and model performance degradation using Evidently.

    Args:
        reference_data: DataFrame of the data used for training the current production model.
        current_data: DataFrame of recent production data.
        column_mapping: Evidently ColumnMapping object.
        model_type: Type of the model ('classification' or 'regression').

    Returns:
        A tuple: (drift_detected_or_performance_degraded, drift_report_summary_json)
    """
    logger.info(
        "Running data drift and model performance check with Evidently...")

    metrics_to_run = [
        DatasetDriftMetric(),
        DataDriftTable(),
    ]

    if model_type == "classification":
        metrics_to_run.append(ClassificationPerformanceMetrics())
    elif model_type == "regression":
        metrics_to_run.append(RegressionPerformanceMetrics())
    else:
        logger.warning(
            f"Unsupported model_type: {model_type}. Skipping performance metrics.")

    drift_report = Report(metrics=metrics_to_run)
    drift_report.run(
        reference_data=reference_data,
        current_data=current_data,
        column_mapping=column_mapping,
    )

    report_json = drift_report.as_dict()

    # Example drift detection logic (customize as needed)
    # DatasetDriftMetric is first
    dataset_drift_score = report_json["metrics"][0]["result"]["drift_score"]
    drift_detected = report_json["metrics"][0]["result"]["drift_detected"]

    logger.info(
        f"Evidently Dataset Drift Score: {dataset_drift_score}, Detected: {drift_detected}")

    # Example performance degradation logic (needs actual model predictions in current_data)
    performance_degraded = False
    if "predictions" in column_mapping.prediction_columns.prediction_column_name and model_type == "classification":
        # Example: Check if F1 score dropped significantly
        # current_f1 = report_json["metrics"][-1]["result"]["current"]["f1"] # Assuming ClassificationPerformanceMetrics is last
        # reference_f1 = report_json["metrics"][-1]["result"]["reference"]["f1"]
        # if reference_f1 and current_f1 < reference_f1 * 0.9: # 10% drop
        #     performance_degraded = True
        #     logger.warning(f"Performance degradation detected: F1 dropped from {reference_f1} to {current_f1}")
        pass  # Placeholder for actual performance check logic

    # Log the full report to MLflow artifacts
    report_path = "evidently_drift_report.json"
    with open(report_path, "w") as f:
        json.dump(report_json, f, indent=4)
    mlflow.log_artifact(report_path)

    summary_for_log = {
        "dataset_drift_score": dataset_drift_score,
        "dataset_drift_detected": drift_detected,
        "performance_degraded": performance_degraded,  # Placeholder
        # Add key performance metrics here
    }

    return drift_detected or performance_degraded, summary_for_log


def run_retraining_logic(
    feast_repo_path: str,
    feature_views: List[str],
    # Path to entities used for training current prod model
    reference_entity_source_path: str,
    current_entity_source_path: str,   # Path to recent entities for drift check
    drift_threshold: float = 0.1,  # Example: if dataset drift score > 0.1
    # Add other training params from train.py if they need to be passed
    **training_kwargs: Any,
):
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(training_kwargs.get(
        "experiment_name", "FX_Model_Retraining"))

    with mlflow.start_run(run_name="DriftCheckAndRetrain") as run:
        logger.info(
            f"Starting MLflow Run for Retraining Logic: {run.info.run_id}")

        fs = FeatureStore(repo_path=feast_repo_path)

        # Load reference and current data (features + labels + predictions if available)
        # This part needs careful implementation:
        # - reference_data: Features + labels from the training set of the *current production model*.
        # - current_data: Recent features + labels + *predictions from the current production model*.
        # For simplicity, we'll assume entity DFs can be used to fetch features,
        # and labels/predictions would need to be added.

        logger.info("Loading reference and current data for drift detection...")
        # Placeholder: these DFs should be prepared with features, target, and prediction columns
        # For a real scenario, you'd fetch features using Feast for both,
        # then add actual labels and predictions from your production model logs.
        ref_entities = pd.read_parquet(reference_entity_source_path)
        curr_entities = pd.read_parquet(current_entity_source_path)

        # This is a simplified representation. You'd need to align columns carefully.
        # reference_data_features = load_features_from_feast(fs, ref_entities, feature_views)
        # current_data_features = load_features_from_feast(fs, curr_entities, feature_views)
        # TODO: Add 'label' and 'prediction' columns to these DataFrames for full Evidently report.

        logger.warning(
            "Drift detection data loading is simplified. Ensure features, labels, and predictions are correctly aligned.")
        # For now, let's assume 'reference_data' and 'current_data' are available with at least features.
        # This is a major simplification for the example.
        # A proper implementation would involve fetching features for both periods,
        # aligning them, and adding actual target and prediction columns.
        # For a pure data drift check on features, this might be okay to start.

        # Example: Using dummy data for structure
        num_features = 10  # Example
        reference_data = pd.DataFrame(np.random.rand(100, num_features), columns=[
                                      f'feature_{i}' for i in range(num_features)])
        reference_data['label'] = np.random.randint(0, 2, 100)
        reference_data['prediction'] = np.random.rand(100)

        current_data = pd.DataFrame(np.random.rand(50, num_features), columns=[
                                    f'feature_{i}' for i in range(num_features)])
        current_data['label'] = np.random.randint(0, 2, 50)
        current_data['prediction'] = np.random.rand(50)

        column_mapping = ColumnMapping()
        column_mapping.target = 'label'
        column_mapping.prediction = 'prediction'
        # column_mapping.numerical_features = [f'feature_{i}' for i in range(num_features)]
        # column_mapping.categorical_features = [] # Add if any

        drift_or_degradation, report_summary = check_drift_and_performance(
            reference_data, current_data, column_mapping, model_type="classification"
        )
        mlflow.log_metrics(report_summary)

        if drift_or_degradation:  # Or use a specific threshold from report_summary
            logger.warning(
                f"Significant drift or performance degradation detected. Triggering retraining.")
            mlflow.log_param("retraining_triggered", True)
            # Trigger the main training script
            # Ensure all necessary arguments for run_training are passed via training_kwargs
            # This assumes run_training will log its own MLflow run.
            run_training(
                feast_repo_path=feast_repo_path,
                feature_views=feature_views,  # Pass through
                entity_source_path=current_entity_source_path,  # Train on up-to-date data
                # Pass other training params like horizon, experiment name etc.
                **training_kwargs
            )
            logger.info("Retraining process completed.")
        else:
            logger.info(
                "No significant drift or degradation detected. Retraining not required.")
            mlflow.log_param("retraining_triggered", False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check for drift and retrain FX Signal Model")
    parser.add_argument("--feast_repo", type=str,
                        default="feature_store", help="Path to Feast repository")
    parser.add_argument("--ref_entities", type=str, required=True,
                        help="Path to Parquet file with entities for reference data")
    parser.add_argument("--curr_entities", type=str, required=True,
                        help="Path to Parquet file with entities for current data")
    # Add other args that need to be passed to run_training if not using defaults
    parser.add_argument("--experiment", type=str, default="FX_Signal_Model_XGBoost",
                        help="MLflow experiment name for training runs")
    parser.add_argument("--horizon", type=int, default=4,
                        help="Labeling horizon for training")

    args = parser.parse_args()

    feature_view_names = [
        "price_technical_features",
    ]

    training_params_for_retrain = {
        "label_horizon": args.horizon,
        "experiment_name": args.experiment,
        # Add other params for run_training as needed
    }

    run_retraining_logic(
        feast_repo_path=args.feast_repo,
        feature_views=feature_view_names,
        reference_entity_source_path=args.ref_entities,
        current_entity_source_path=args.curr_entities,
        **training_params_for_retrain
    )
