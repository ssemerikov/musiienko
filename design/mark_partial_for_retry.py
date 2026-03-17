#!/usr/bin/env python3
"""Mark partial cases for retry by removing them from completed_cases"""

import json
from pathlib import Path

# Find the latest checkpoint
checkpoint_dir = Path("/home/cc/claude_code/design/checkpoints")
checkpoints = sorted(checkpoint_dir.glob("naqa_022*.json"), key=lambda x: x.stat().st_mtime)
if not checkpoints:
    print("No checkpoints found")
    exit(1)

latest = checkpoints[-1]
print(f"Using checkpoint: {latest}")

# Load checkpoint
with open(latest) as f:
    data = json.load(f)

# Find partial case IDs from raw data
raw_dir = Path("/home/cc/claude_code/design/data/raw")
partial_ids = []
for json_file in raw_dir.glob("case_*.json"):
    with open(json_file) as f:
        case_data = json.load(f)
        if case_data.get("scrape_status") == "partial":
            case_id = case_data.get("case_id")
            if case_id:
                partial_ids.append(case_id)

print(f"Found {len(partial_ids)} partial cases")

# Remove partial cases from completed_cases
completed = set(data.get("completed_cases", []))
original_count = len(completed)
for case_id in partial_ids:
    completed.discard(case_id)

data["completed_cases"] = list(completed)
removed_count = original_count - len(completed)
print(f"Removed {removed_count} cases from completed_cases")

# Mark partial cases as failed so they can be retried
# failed_cases should be a dict {case_id: error_message}
failed = data.get("failed_cases", {})
if isinstance(failed, list):
    failed = {}
for case_id in partial_ids:
    failed[case_id] = "partial - needs retry with direct URL"
data["failed_cases"] = failed
print(f"Marked {len(partial_ids)} cases as failed for retry")

# Save updated checkpoint
with open(latest, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Updated checkpoint saved: {latest}")
