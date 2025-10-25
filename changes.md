#change #1

**Refactor: Improve GitHub Actions Monitoring for Reliability and UX**

This commit completely overhauls the workflow monitoring logic in `github.py` to fix critical reliability issues and improve user feedback.

**Key Changes:**

1.  **Robust Run Identification:**
    *   The script now correctly locates the triggered workflow run by matching a unique UUID in the `run-name` property.
    *   **Problem Solved:** This eliminates a race condition where the script could mistakenly track the wrong workflow if multiple jobs were started simultaneously. It relies on the corresponding change in the `.github/workflows/armv1.yml` file.

2.  **Resilient Polling Mechanism:**
    *   The fragile `gh run watch` command has been completely removed and replaced with a polling loop that uses `gh run view`.
    *   **Problem Solved:** This makes the monitoring process immune to temporary network failures, fixing the `connection reset by peer` error that would previously crash the script.

3.  **Enhanced User Feedback:**
    *   The new polling loop provides a clean, single-line status that updates in place, showing the user the overall status (`in_progress`, etc.) and the name of the specific step currently executing.
    *   **Problem Solved:** This gives the user clear, real-time feedback on the job's progress without the messy, verbose output of `gh run watch`, directly addressing the desire for better "user satisfaction."
