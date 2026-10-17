
#!/usr/bin/env bash
set -euo pipefail

RAW_BASE="/telcocore/raw/telecom"

upload_directory() {
    local source_dir="$1"
    local target_dir="$2"

    docker compose exec -T namenode \
        hdfs dfs -mkdir -p "$target_dir"

    for file in "$source_dir"/*.csv; do
        [ -f "$file" ] || continue

        filename=$(basename "$file")

        echo "Uploading: $filename"

        docker compose exec -T namenode \
            hdfs dfs -put -f - \
            "$target_dir/$filename" < "$file"

        echo "Uploaded: $filename"
    done
}

upload_directory \
    "data/batch" \
    "$RAW_BASE/batch"

upload_directory \
    "data/reference" \
    "$RAW_BASE/reference"

echo "TELCOCORE_BATCH_INGESTION_COMPLETED"
