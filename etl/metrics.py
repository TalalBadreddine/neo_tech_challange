from prometheus_client import Counter, Histogram, Gauge

PROCESSED_RECORDS = Counter(
    'etl_processed_records_total',
    'Number of records processed',
    ['processor_type', 'status']
)

PROCESSING_TIME = Histogram(
    'etl_processing_duration_seconds',
    'Time spent processing records',
    ['processor_type', 'operation']
)

ACTIVE_JOBS = Gauge(
    'etl_active_jobs',
    'Number of currently running ETL jobs',
    ['processor_type']
)

ERROR_COUNT = Counter(
    'etl_errors_total',
    'Number of ETL errors',
    ['processor_type', 'error_type']
)

MEMORY_USAGE = Gauge(
    'etl_memory_usage_bytes',
    'Memory usage of ETL process',
    ['processor_type']
)