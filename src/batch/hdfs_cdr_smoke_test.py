
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Initialize Spark Application
spark = (
    SparkSession.builder
    .appName("TelcoCore-HDFS-CDR-Smoke-Test")
    .getOrCreate()
)

# Telecom CDR data stored in HDFS
HDFS_PATH = (
    "hdfs://namenode:9000"
    "/telcocore/bronze/cdr/cdr_sample.csv"
)

# Explicit schema for telecom CDRs
CDR_SCHEMA = """
    cdr_id STRING,
    subscriber_id STRING,
    event_type STRING,
    duration_sec INT,
    cell_id STRING
"""

try:
    # Read data from HDFS
    cdr_df = (
        spark.read
        .option("header", "true")
        .schema(CDR_SCHEMA)
        .csv(HDFS_PATH)
    )

    print("=== CDR SCHEMA ===")
    cdr_df.printSchema()

    print("=== ALL CDR RECORDS ===")
    cdr_df.show(truncate=False)

    # Transformation: filter voice calls
    voice_df = cdr_df.filter(
        col("event_type") == "VOICE"
    )

    print("=== VOICE CALLS ===")
    voice_df.show(truncate=False)

    # Actions trigger Spark execution
    total_records = cdr_df.count()
    voice_records = voice_df.count()

    print(f"Total Records: {total_records}")
    print(f"Voice Records: {voice_records}")

    assert total_records == 3
    assert voice_records == 1

    print("TELCOCORE_SPARK_HDFS_TEST_PASSED")

finally:
    spark.stop()
