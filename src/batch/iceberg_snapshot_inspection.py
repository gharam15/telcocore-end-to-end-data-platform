
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("TelcoCore-Iceberg-Snapshot-Inspection")
    .getOrCreate()
)

try:
    print("=== TABLE SNAPSHOTS ===")

    spark.sql("""
        SELECT
            snapshot_id,
            committed_at,
            operation,
            summary
        FROM telcocore.bronze.cdr_events.snapshots
        ORDER BY committed_at
    """).show(truncate=False)

    print("=== TABLE HISTORY ===")

    spark.sql("""
        SELECT
            made_current_at,
            snapshot_id,
            is_current_ancestor
        FROM telcocore.bronze.cdr_events.history
        ORDER BY made_current_at
    """).show(truncate=False)

    print("=== DATA FILES ===")

    spark.sql("""
        SELECT
            file_path,
            file_format,
            record_count
        FROM telcocore.bronze.cdr_events.files
    """).show(truncate=False)

    print("TELCOCORE_ICEBERG_METADATA_INSPECTION_PASSED")

finally:
    spark.stop()
