import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import great_expectations as gx
import pandas as pd
from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult

from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)


class DataValidationError(Exception):
    """Custom exception for data validation failures."""

    def __init__(self, message: str, validation_result: Optional[CheckpointResult] = None):
        super().__init__(message)
        self.validation_result = validation_result


class DataValidator:
    def __init__(self, context_root_dir: str = "great_expectations"):
        self.context_root_dir = Path(context_root_dir)
        try:
            self.context = gx.get_context(
                context_root_dir=str(self.context_root_dir))
            logger.info(
                f"Great Expectations context loaded from: {self.context_root_dir.resolve()}")
        except Exception as e:
            logger.error(
                f"Failed to load Great Expectations context from {self.context_root_dir}: {e}")
            logger.warning(
                "Ensure Great Expectations is initialized in the specified directory. "
                "Run 'great_expectations init' in the 'great_expectations' folder if needed."
            )
            raise

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        expectation_suite_name: str,
        checkpoint_name: Optional[str] = None,
        batch_identifier_data: Optional[Dict[str, Any]] = None,
    ) -> CheckpointResult:
        """
        Validates a Pandas DataFrame against a specified Expectation Suite.

        Args:
            df: The DataFrame to validate.
            expectation_suite_name: The name of the Expectation Suite to use.
            checkpoint_name: Optional. If provided, runs a pre-configured Checkpoint.
                             Otherwise, a runtime checkpoint is created.
            batch_identifier_data: Optional. Data to identify the batch, e.g., {"timestamp": "2023-01-01"}.

        Returns:
            The CheckpointResult object.

        Raises:
            DataValidationError: If validation fails.
        """
        if batch_identifier_data is None:
            batch_identifier_data = {"timestamp": datetime.now().isoformat()}

        data_asset_name = f"{expectation_suite_name}_asset_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            if checkpoint_name:
                logger.info(
                    f"Running checkpoint: {checkpoint_name} for suite: {expectation_suite_name}")
                # For pre-configured checkpoints, the data asset might be defined in the checkpoint
                # This example assumes we pass the dataframe directly to the checkpoint's run method
                # This might require specific checkpoint configuration.
                # A more common way for pre-configured checkpoints is to point them to a data source.
                # For dynamic dataframes, runtime checkpoints are often easier.
                result: CheckpointResult = self.context.run_checkpoint(
                    checkpoint_name=checkpoint_name,
                    batch_request=None,  # Or configure appropriately
                    run_name_template=f"%Y%m%d-%H%M%S-{expectation_suite_name}-run",
                    validations=[
                        {
                            "batch_request": self.context.get_batch_request(
                                # Ensure this datasource exists or is created
                                datasource_name="runtime_pandas_datasource",
                                data_connector_name="default_runtime_data_connector_name",
                                data_asset_name=data_asset_name,
                                runtime_parameters={"batch_data": df},
                                batch_identifiers=batch_identifier_data,
                            ),
                            "expectation_suite_name": expectation_suite_name,
                        }
                    ]
                )
            else:
                logger.info(
                    f"Running runtime validation for suite: {expectation_suite_name}")
                validator = self.context.sources.add_pandas("runtime_pandas_datasource").read_dataframe(
                    df,
                    asset_name=data_asset_name,
                    batch_identifiers=batch_identifier_data
                )
                result = validator.validate(
                    expectation_suite_name=expectation_suite_name)

            if not result.success:
                logger.error(
                    f"Data validation failed for suite {expectation_suite_name}. "
                    f"Success: {result.success}"
                )
                # For detailed logging of failures:
                for run_result in result.run_results.values():
                    for validation_result in run_result["validation_result"].results:
                        if not validation_result.success:
                            logger.warning(f"Failed expectation: {validation_result.expectation_config.expectation_type} "
                                           f"with params: {validation_result.expectation_config.kwargs} -> "
                                           f"Observed: {validation_result.result.get('observed_value')}")
                raise DataValidationError(
                    f"Validation failed for {expectation_suite_name}", validation_result=result
                )

            logger.info(
                f"Data validation successful for suite {expectation_suite_name}.")
            return result

        except Exception as e:
            logger.error(
                f"Error during data validation for suite {expectation_suite_name}: {e}")
            if isinstance(e, DataValidationError):
                raise
            raise DataValidationError(
                f"An unexpected error occurred during validation: {str(e)}")

# Example Usage (you would call this from your orchestration pipeline)
# if __name__ == "__main__":
#     # This is a placeholder. You'd typically initialize GE context first.
#     # `great_expectations init` in the `great_expectations` directory.
#     # Then create expectation suites.
#     try:
#         validator = DataValidator(context_root_dir="great_expectations")
#         # Create a sample DataFrame (replace with actual data loading)
#         sample_data = {'col1': [1, 2, 3, None, 5], 'col2': ['a', 'b', 'c', 'd', 'e'], 'timestamp': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'])}
#         sample_df = pd.DataFrame(sample_data)

#         # Assume you have an expectation suite named "my_suite"
#         # You would create this using `great_expectations suite new`
#         # validator.validate_dataframe(sample_df, "my_suite")
#         logger.info("To run this example, first initialize Great Expectations and create a suite.")
#     except Exception as e:
#         logger.error(f"Failed to run validation example: {e}")
