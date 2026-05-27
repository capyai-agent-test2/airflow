Dag processor metrics now normalize Dag file names before emitting ``dag_processing.last_run.seconds_ago`` so file paths with spaces or other invalid characters no longer trip the metrics validator.
