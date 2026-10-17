
import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path("data/batch")

def read_csv(filename):
    with (DATA_DIR / filename).open(
        newline="", encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f))

subscribers = read_csv("subscribers.csv")
monthly_usage = read_csv("monthly_usage.csv")
app_usage = read_csv("app_usage.csv")

subscriber_ids = {
    row["subscriber_id"]
    for row in subscribers
}

assert len(subscriber_ids) == len(subscribers), (
    "Duplicate subscriber IDs detected"
)

monthly_keys = {
    (row["subscriber_id"], row["month"])
    for row in monthly_usage
}

app_totals = defaultdict(int)

for row in app_usage:
    subscriber_id = row["subscriber_id"]
    month = row["usage_month"]
    usage_mb = int(row["mobile_data_mb"])

    assert subscriber_id in subscriber_ids
    assert (subscriber_id, month) in monthly_keys
    assert usage_mb >= 0

    app_totals[(subscriber_id, month)] += usage_mb

assert set(app_totals) == monthly_keys, (
    "Missing or unexpected subscriber-months"
)

# Reconcile app usage against monthly usage
for row in monthly_usage:
    key = (row["subscriber_id"], row["month"])

    expected_mb = round(float(row["data_used_gb"]) * 1024)
    actual_mb = app_totals[key]

    assert abs(actual_mb - expected_mb) <= 1, (
        f"Usage mismatch for {key}: "
        f"apps={actual_mb} MB, monthly={expected_mb} MB"
    )


# Verify app-level totals against monthly usage
for row in monthly_usage:
    key = (row["subscriber_id"], row["month"])

    expected_mb = round(
        float(row["data_used_gb"]) * 1024
    )

    actual_mb = app_totals[key]

    assert abs(actual_mb - expected_mb) <= 1, (
        f"Usage mismatch for {key}: "
        f"apps={actual_mb}, expected={expected_mb}"
    )


print("Monthly usage reconciliation: PASSED")

print("Subscribers:", len(subscribers))
print("Monthly Usage:", len(monthly_usage))
print("App Usage Records:", len(app_usage))
print("Subscriber relationships: PASSED")
print("Monthly relationships: PASSED")
print("Non-negative app usage: PASSED")
print("TELCOCORE_APP_USAGE_QUALITY_PASSED")
