
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("TelcoCore-Iceberg-Bronze-Test")
    .getOrCreate()
)

try:
    # Create Bronze namespace
    spark.sql("""
        CREATE NAMESPACE IF NOT EXISTS telcocore.bronze
    """)

    # Create Iceberg table
    spark.sql("""
        CREATE TABLE IF NOT EXISTS
        telcocore.bronze.cdr_events (
            cdr_id STRING,
            subscriber_id STRING,
            event_type STRING,
            duration_sec INT,
            cell_id STRING
        )
        USING iceberg
    """)

    # Read raw CSV from HDFS
    raw_df = (
        spark.read
        .option("header", "true")
        .schema("""
            cdr_id STRING,
            subscriber_id STRING,
            event_type STRING,
            duration_sec INT,
            cell_id STRING
        """)
        .csv(
            "hdfs://namenode:9000/"
            "telcocore/bronze/cdr/cdr_sample.csv"
        )
    )

    # Overwrite sample table for repeatable test
    raw_df.writeTo(
        "telcocore.bronze.cdr_events"
    ).overwritePartitions()

    # Query Iceberg table
    result = spark.sql("""
        SELECT event_type, COUNT(*) AS total_events
        FROM telcocore.bronze.cdr_events
        GROUP BY event_type
        ORDER BY event_type
    """)

    result.show()

    assert spark.table(
        "telcocore.bronze.cdr_events"
    ).count() == 3

    print("TELCOCORE_ICEBERG_BRONZE_TEST_PASSED")

finally:
    spark.stop()
