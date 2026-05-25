``airflow connections test`` now reuses the already-loaded SQL connection object instead of looking it up a second time during hook-based connection tests.
