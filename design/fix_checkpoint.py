#!/usr/bin/env python3
"""Fix checkpoint to use proper failed_cases format"""

import json
from pathlib import Path

checkpoint_file = Path("/home/cc/claude_code/design/checkpoints/naqa_022_20260130_001311_6906cdc9.json")

with open(checkpoint_file) as f:
    data = json.load(f)

# Convert failed_cases dict to list format
failed = data.get("failed_cases", {})
if isinstance(failed, dict):
    # Convert to list format: [{"case_id": "123", "error": "..."}]
    failed_list = [{"case_id": k, "error": v} for k, v in failed.items()]
    data["failed_cases"] = failed_list
    print(f"Converted {len(failed_list)} failed cases to list format")

with open(checkpoint_file, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Checkpoint fixed")
