#!/usr/bin/env python3
"""Clear failed_cases to allow retry"""

import json
from pathlib import Path

checkpoint_file = Path("/home/cc/claude_code/design/checkpoints/naqa_022_20260130_001311_6906cdc9.json")

with open(checkpoint_file) as f:
    data = json.load(f)

print(f"Before: {len(data.get('completed_cases', []))} completed, {len(data.get('failed_cases', []))} failed")

# Clear failed cases so they become pending
data["failed_cases"] = []

print(f"After: {len(data.get('completed_cases', []))} completed, {len(data.get('failed_cases', []))} failed")

# Count pending
all_ids = {u["case_id"] for u in data.get("case_urls", [])}
completed_ids = set(data.get("completed_cases", []))
pending = all_ids - completed_ids
print(f"Pending cases: {len(pending)}")

with open(checkpoint_file, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Checkpoint updated")
