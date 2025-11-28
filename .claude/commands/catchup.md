---
description: Smart context restore - reads all modified and new files.
---

# Context Restoration Protocol

You need to re-sync with the project state.

1.  **Scan Git State**:
    - Run `git status -s` to find all modified (`M`) and untracked (`??`) files.
2.  **Ingest Content**:
    - For every file listed above, read its content immediately.
3.  **Ready State**:
    - Once read, confirm by saying: "Context synced. I see changes in [file_list]. Ready to proceed."
