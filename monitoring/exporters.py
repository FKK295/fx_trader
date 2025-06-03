from prometheus_client import Counter, Gauge, Histogram, Summary

# --- Core Trading Metrics ---
PNL_TOTAL = Gauge(
    "fx_trader_pnl_total_usd", "Total Profit and Loss in USD"
)
CURRENT_DRAWDOWN_PCT = Gauge(
    "fx_trader_current_drawdown_percentage", "Current portfolio drawdown percentage"
)
OPEN_TRADES_COUNT = Gauge(
    "fx_trader_open_trades_count", "Number of currently open trades", ["pair"]
)
TRADE_DURATION_SECONDS = Histogram(
    "fx_trader_trade_duration_seconds", "Duration of closed trades in seconds", [
        "pair", "strategy"]
)
SLIPPAGE_BPS = Histogram(
    "fx_trader_slippage_basis_points", "Slippage experienced in basis points per trade", [
        "pair"]
)

# --- API Interaction Metrics ---
API_CALL_LATENCY_SECONDS = Histogram(
    "fx_trader_api_call_latency_seconds", "Latency of external API calls", [
        "api_name", "endpoint"]
)
API_CALL_ERRORS_TOTAL = Counter(
    "fx_trader_api_call_errors_total", "Total number of external API call errors", [
        "api_name", "endpoint", "error_type"]
)

# --- System Health & Operations ---
ORDER_EVENTS_TOTAL = Counter(
    "fx_trader_order_events_total", "Total number of order events", [
        "pair", "order_type", "status"]
)  # status: e.g. created, filled, cancelled, rejected
RISK_MANAGEMENT_TRIGGERS_TOTAL = Counter(
    "fx_trader_risk_management_triggers_total", "Total times a risk management rule was triggered", [
        "rule_type"]
)  # rule_type: e.g., max_drawdown, max_positions

APPLICATION_ERRORS_TOTAL = Counter(
    "fx_trader_application_errors_total", "Total number of unhandled application errors", [
        "module", "function"]
)

DATA_INGESTION_BATCH_SIZE = Gauge(
    "fx_trader_data_ingestion_batch_size", "Number of records in the last ingested batch", [
        "data_source"]
)
DATA_INGESTION_LATENCY_SECONDS = Summary(
    "fx_trader_data_ingestion_latency_seconds", "Latency of data ingestion process", [
        "data_source"]
)

# --- Model Monitoring Metrics (from Evidently or custom) ---
MODEL_DRIFT_SCORE = Gauge(
    "fx_trader_model_drift_score", "Drift score for the production model", [
        "model_name", "drift_type"]  # drift_type: data, concept
)
MODEL_PREDICTION_CONFIDENCE = Histogram(
    "fx_trader_model_prediction_confidence", "Distribution of model prediction confidence scores", [
        "model_name"]
)

# You would increment/set these metrics from relevant parts of your codebase.
# Example: PNL_TOTAL.set(current_pnl)
#          API_CALL_ERRORS_TOTAL.labels(api_name='oanda', endpoint='/orders', error_type='timeout').inc()
