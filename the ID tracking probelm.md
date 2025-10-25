## Programmatically Triggering GitHub Actions and Retrieving the Run ID: A Comprehensive Analysis

GitHub Actions' `workflow_dispatch` endpoint returns an empty 204 response without a run ID, creating a fundamental challenge for automation scripts that need to monitor workflow progress. This is a well-documented limitation that has persisted for years, with GitHub acknowledging it as a technical challenge due to the asynchronous webhook-based architecture.[1][2][3]

### The Core Problem

When you trigger a workflow using `gh workflow run` or the GitHub API's `POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches` endpoint, the response contains no identifier linking your request to the resulting workflow run. GitHub explained that at the time of the API call, the run hasn't been created yet because `workflow_dispatch` events are processed asynchronously like other webhooks. While multiple community members have proposed solutions (such as attaching a UUID to the dispatch request and returning it in the response), GitHub has not implemented this feature as of October 2024.[2][4][5][6][1]

### Solution 1: The Polling Method

**How it works:** This approach involves capturing the most recent run ID before triggering, dispatching the workflow, then polling `gh run list` until a newer run ID appears.[7][1]

**Implementation considerations:**

The basic algorithm queries for runs created after a timestamp (typically current time minus 5 minutes) and filters by workflow ID, branch, and event type (`workflow_dispatch`). A Python implementation would look like this:[8][1]

```python
import datetime
import time
import requests

# Get current timestamp minus buffer
delta_time = datetime.timedelta(minutes=5)
run_date_filter = (datetime.datetime.utcnow()-delta_time).strftime("%Y-%m-%dT%H:%M")

# Trigger workflow
requests.post(f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches",
    headers=authHeader,
    json={"ref":"main"})

# Poll for new run
workflow_id = ""
while workflow_id == "":
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/actions/runs?created=>{run_date_filter}",
        headers=authHeader)
    runs = r.json()["workflow_runs"]
    # Filter and identify your run...
    time.sleep(3)
```

**Reliability analysis:**

This method has critical race condition vulnerabilities in high-velocity repositories:[9][1][2]

- **Concurrent triggers:** If another workflow of the same type is triggered within your polling window, you may capture the wrong run ID[1][9]
- **Fast completion:** If the workflow completes before your first poll, it might not appear in pending runs[2]
- **Multiple simultaneous dispatches:** Team environments with multiple developers or automated systems triggering workflows simultaneously make this approach unreliable[10][1]

**Performance:** Polling typically resolves within 10-30 seconds with 3-5 second intervals, though edge cases can take longer. The method is API-intensive, making multiple requests per dispatch attempt.[8][2]

**Best practices:** The `convictional/trigger-workflow-and-wait` action implements a more robust polling algorithm that matches runs by timestamp, branch, and workflow file, with configurable retry intervals. However, even this improved implementation acknowledges it cannot be made fully robust against race conditions.[4][11][10]

### Solution 2: Direct GitHub API Call

**How it works:** Using the REST API or libraries like PyGithub/requests to call `POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches`.[6][12][13]

**API Response analysis:**

The official GitHub API documentation explicitly states the response is `Status: 204` with **no content**. This is consistent across all implementations:[6]

- **Response body:** Empty
- **Response headers:** Do not contain run ID or location headers pointing to the created run[3][6]
- **PyGithub:** The `create_workflow_dispatch()` method in PyGithub returns `None` as it simply wraps the REST API call[14][15]

**Conclusion:** This method provides no advantage over using `gh workflow run` — both use the same underlying API that returns no run identifier. Any solution using the API must still implement polling or another correlation mechanism.[3][1][6]

### Solution 3: Filtering with a Unique Input Identifier

**How it works:** This is the most reliable workaround currently available. It involves:

1. Generating a unique identifier (UUID) before triggering
2. Passing it as a workflow input
3. Configuring the target workflow to display this UUID in a step name
4. Polling workflow jobs and matching the UUID in step names to identify your specific run[16][17][1][8]

**Implementation requirements:**

**Dispatching workflow (caller):**
```bash
# Generate unique ID
WORKFLOW_ID=$(uuidgen)

# Trigger with input
gh workflow run deploy.yml -f id="$WORKFLOW_ID"

# Poll and match
while [ -z "$RUN_ID" ]; do
  RUN_ID=$(gh api "repos/$OWNER/$REPO/actions/runs?created=>$DATE_FILTER" \
    | jq -r ".workflow_runs[] | select(.name | contains(\"$WORKFLOW_ID\")) | .id")
  sleep 5
done
```

**Target workflow (receiver):**
```yaml
name: Deploy
on:
  workflow_dispatch:
    inputs:
      id:
        description: 'Unique run identifier'
        required: false

jobs:
  identify:
    name: Workflow ID Provider
    runs-on: ubuntu-latest
    steps:
      - name: ${{ github.event.inputs.id }}
        run: echo "Run identifier ${{ inputs.id }}"
```

The critical component is using the UUID in the **step name** (`name: ${{ github.event.inputs.id }}`), which makes it queryable via the API.[16][1][8]

**Reliability analysis:**

This method is **significantly more reliable** than basic polling:[17][18][16]

- **Uniqueness guarantee:** UUIDs provide cryptographic-level uniqueness, eliminating false matches[17][8]
- **Race condition mitigation:** Even with concurrent triggers, each dispatch has a distinct identifier[16][17]
- **Verification:** You can definitively confirm you're tracking the correct run[1][8]

**Performance:** Similar polling overhead to Method 1, but with higher confidence in results. The `lasith-kg/dispatch-workflow` action implements an "efficient and accurate correlation algorithm" using this UUID injection technique and claims to be more performant than alternatives. The `codex-/return-dispatch` action (the original implementation of this approach) has been proven in production use and includes configurable retry logic with linear backoff.[19][20][17][16]

**Limitations:**

- Requires modifying the target workflow to accept and display the UUID input[1][16]
- Still depends on polling; the UUID doesn't eliminate the async nature, just makes correlation accurate[17][1]
- The workflow must start and reach the first step before the UUID becomes visible via the API[8]

### Recommended Solution: UUID-Based Correlation with Existing Actions

For **production environments requiring reliability**, use the UUID input method via battle-tested GitHub Actions:

1. **`lasith-kg/dispatch-workflow@v2`** — Supports both `workflow_dispatch` and `repository_dispatch`, with an optimized discovery algorithm[19][17]
2. **`codex-/return-dispatch@v2`** — The original implementation, supports `workflow_dispatch` only, well-maintained[20][16]

Both actions handle the complexity of UUID generation, injection, polling, and correlation, exposing the `run_id` as an output you can use in subsequent steps.[16][17]

**Example usage:**
```yaml
steps:
  - uses: lasith-kg/dispatch-workflow@v2
    id: dispatch
    with:
      dispatch-method: workflow_dispatch
      repo: target-repo
      owner: target-owner
      workflow: deploy.yml
      token: ${{ secrets.PAT_TOKEN }}
      discover: true  # Enables run ID discovery
      
  - name: Monitor workflow
    run: |
      echo "Triggered run: ${{ steps.dispatch.outputs.run_id }}"
      echo "URL: ${{ steps.dispatch.outputs.run_url }}"
```

For **Python automation scripts outside GitHub Actions**, implement the UUID correlation manually following the pattern demonstrated in the search results, or use the GitHub CLI in a subprocess with the same UUID technique.[8]

### Why Not Use Basic Polling Alone?

While basic polling (Method 1) works in **low-velocity, single-developer repositories**, it fails catastrophically when:[9][10][1]

- Multiple CI/CD pipelines trigger the same workflow concurrently
- Teams have multiple developers or automated systems
- The repository has high commit frequency
- You need guaranteed correctness for critical deployments

The UUID approach adds minimal complexity but provides **deterministic identification** — the difference between "probably the right run" and "definitely the right run".[17][1][16]

### GitHub's Position and Future Outlook

GitHub has acknowledged this limitation since at least 2021 but has not provided a timeline for native support. The issue remains open in community discussions with hundreds of upvotes. Community members have proposed elegant solutions (adding a `dispatch_uuid` to the response), but GitHub's internal feature request was reportedly closed without implementation.[18][4][2]

Until GitHub provides native support, the UUID correlation method remains the **canonical, most robust solution** for programmatically obtaining run IDs after workflow dispatch.[1][16][17]
