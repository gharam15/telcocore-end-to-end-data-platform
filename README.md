
# TelcoCore
## End-to-End Telecom Big Data Engineering & Analytics Platform

An enterprise-oriented data engineering project for batch and
real-time telecom analytics.

### Technology Stack
- Apache Hadoop HDFS
- Apache Spark
- Apache Kafka
- Apache Iceberg
- Apache Hive
- Apache Airflow
- Docker & Docker Compose
- Prometheus & Grafana

### Architecture
Telecom Sources → Batch / Streaming → HDFS + Iceberg
→ Bronze → Silver → Gold → SQL Analytics

### Implementation Progress
- [x] Docker and WSL environment
- [x] Hadoop HDFS initial setup
- [x] NameNode and DataNode registration
- [x] HDFS write/read smoke test
- [x] HDFS FSCK validation
- [ ] Apache Spark
- [ ] Apache Iceberg
- [ ] Apache Kafka
- [ ] Apache Hive
- [ ] Governance and Monitoring

### HDFS Validation
Sample: data/samples/cdr_sample.csv

Result: HEALTHY
Live DataNodes: 1
Missing Blocks: 0

Note: Single DataNode setup for local development.
