from prometheus_client import Counter, Gauge, Histogram

BACKGROUND_JOB_RUNS = Counter("stock_signal_background_job_runs_total", "Background jobs.", ("job_type", "status"))
BACKGROUND_JOB_DURATION = Histogram("stock_signal_background_job_duration_seconds", "Background-job duration.", ("job_type",))
BACKGROUND_JOB_ITEMS = Counter("stock_signal_background_job_items_total", "Items processed.", ("job_type", "outcome"))
BACKGROUND_JOB_LAST_SUCCESS = Gauge("stock_signal_background_job_last_success_timestamp_seconds", "Most recent success.", ("job_type",))
BACKGROUND_JOB_ACTIVE = Gauge("stock_signal_background_job_active", "Active background jobs.", ("job_type",))
BACKGROUND_JOB_DEAD_LETTERS = Counter("stock_signal_background_job_dead_letters_total", "Dead-letter jobs.", ("job_type", "error_type"))
BACKGROUND_SWEEP_CANDIDATES = Gauge("stock_signal_background_sweep_candidates", "Latest sweep candidates.", ("job_type",))
