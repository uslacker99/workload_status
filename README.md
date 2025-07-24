# PCE Workload Status Script

## Overview
This Python script retrieves workload information from a Policy Compute Engine (PCE) API, processes workload states, and generates a detailed report in both console output and a CSV file (`/tmp/out.csv`). The script supports pagination, handles asynchronous API responses, and includes counts for workload states, agent statuses, policy sync states, and two additional counts:
- **Active Syncing**: Number of online workloads with `security_policy_sync_state` set to `"syncing"`.
- **Offline, Will Sync When Online**: Number of offline workloads that are managed and not uninstalled, expected to sync when they come back online.

The script is designed to work with the PCE API, using HTTP Basic Authentication and handling API responses with retry logic based on the `Retry-After` header.

## Features
- **Workload Retrieval**: Fetches all workloads from the PCE API (`/orgs/{ORG}/workloads`) with pagination support.
- **Comprehensive Reporting**: Displays workload details (hostname, IP, state, agent status, policy sync, enforcement mode, status, version, health errors, managed since) in a formatted console table and CSV file.
- **State and Status Parsing**:
  - Determines workload state (`offline`, `unmanaged`, `uninstalled`, `idle`, `visibility`, `enforced`, `active`, `active/syncing`) based on `online`, `managed`, `enforcement_mode`, and `config_sync_state`.
  - Determines agent status (`offline`, `uninstalled`, `stopped`, `active`, `active/syncing`, `unknown`) based on `online` and `agent.status`.
- **Summary Counts**:
  - **State Counts**: Number of workloads in each state (e.g., `active`, `offline`, `active/syncing`).
  - **Agent Status Counts**: Number of workloads by agent status (e.g., `active`, `offline`).
  - **Policy Sync Counts**: Number of workloads by `security_policy_sync_state` (e.g., `syncing`, `N/A`).
  - **Active Syncing Count**: Counts online workloads with `security_policy_sync_state == "syncing"`.
  - **Offline, Will Sync When Online Count**: Counts offline, managed workloads with an installed agent (not `uninstalled`).
- **Retry Logic**: Handles asynchronous API responses (HTTP 202) with up to 50 retries, using the `Retry-After` header for wait times between retries.
- **Error Handling**: Gracefully handles API errors, JSON decoding issues, and invalid workload data.

## Prerequisites
- **Python**: Version 3.6 or higher.
- **Dependencies**: Install required Python packages using:
  ```bash
  pip install requests
  ```
- **PCE API Access**:
  - A valid PCE server URL (e.g., `https://pce.shocknetwork.com:8443`).
  - API credentials (username and password).
  - Organization ID (`ORG`).

## Installation
1. Clone or download the script to your local machine.
2. Install dependencies:
   ```bash
   pip install requests
   ```
3. Update the script’s configuration variables at the top:
   - `LOGIN`: Your PCE API username (e.g., `"api_19904f5c9e50161eb"`).
   - `PASSWD`: Your PCE API password.
   - `SERVER`: The PCE server URL (e.g., `"https://pce.shocknetwork.com:8443"`).
   - `ORG`: Your organization ID (e.g., `"1"`).
   - `CSV_FILE`: Output CSV file path (default: `"/tmp/out.csv"`).

## Usage
Run the script using Python:
```bash
python3 pce_workload_status.py
```

### Output
- **Console Output**:
  - Displays a table of workload details, including hostname, IP, state, agent status, policy sync, enforcement mode, status, version, health errors, and managed since date.
  - Shows a summary section with:
    - State Counts (e.g., `active`, `offline`, `active/syncing`).
    - Agent Status Counts (e.g., `active`, `offline`).
    - Policy Sync Counts (e.g., `syncing`, `N/A`).
    - Additional Counts:
      - Active Syncing: Online workloads with `security_policy_sync_state == "syncing"`.
      - Offline, Will Sync When Online: Offline, managed, non-uninstalled workloads.
- **CSV Output**:
  - Saves workload details to `/tmp/out.csv` with the same columns as the console table.
  - Appends the summary counts (state, agent status, policy sync, and additional counts) at the end of the CSV file.

### Example Output
**Console**:
```
Total workloads retrieved: 10

Workload Status:
==================================================================================================================================
Hostname             IP              State        Agent Status Policy Sync  Mode         Status       Version    Health Errors   Managed Since
==================================================================================================================================
server1             192.168.1.1     active       active       syncing      enforced     running      1.2.3      None            2025-01-01
server2             192.168.1.2     offline      offline      N/A          idle         N/A          N/A        None            2025-01-02
...

Summary:
==================================================
State Counts:
active              : 5
active/syncing      : 2
offline             : 3

Agent Status Counts:
active              : 5
active/syncing      : 2
offline             : 3

Policy Sync Counts:
syncing             : 2
N/A                 : 8

Additional Counts:
Active Syncing      : 2
Offline, Will Sync When Online: 3
```

**CSV** (`/tmp/out.csv`):
```csv
Hostname,IP,State,Agent Status,Policy Sync,Mode,Status,Version,Health Errors,Managed Since
server1,192.168.1.1,active,active,syncing,enforced,running,1.2.3,None,2025-01-01
server2,192.168.1.2,offline,offline,N/A,idle,N/A,N/A,None,2025-01-02
...
,Summary
,State,Count
,active,5
,active/syncing,2
,offline,3
,,Agent Status,Count
,active,5
,active/syncing,2
,offline,3
,,Policy Sync,Count
,syncing,2
,N/A,8
,,Additional Counts
,Active Syncing,2
,Offline, Will Sync When Online,3
```

## Configuration
Edit the following variables in the script to match your PCE environment:
```python
LOGIN = "api_19b"  # Your PCE API username
PASSWD = "75df7f70b42c0d8075"  # Your PCE API password
SERVER = "https://pce.shocknetwork.com:8443"  # PCE server URL
ORG = "1"  # Organization ID
CSV_FILE = "/tmp/out.csv"  # Output CSV file path
```

## Notes
- **Retry Logic**: The script retries API job status checks up to 50 times, using the `Retry-After` header value (defaulting to 1 second) for wait times between retries.
- **Offline Workloads**: Included in the report and counted in `offline_will_sync_count` if managed and not uninstalled. Excluded from `active_syncing_count`.
- **Active Syncing Count**: Only counts online workloads with `security_policy_sync_state == "syncing"`.
- **Security**: Store API credentials securely (e.g., use environment variables or a configuration file instead of hardcoding).
- **Debugging**: If `active_syncing_count` is 0, check the `Policy Sync` column and `Policy Sync Counts` in the output to verify if any workloads have `security_policy_sync_state == "syncing"`. Add debug prints in the `fetch_and_display_workloads` function to inspect raw API data if needed.

## Troubleshooting
- **API Errors**: Ensure the `LOGIN`, `PASSWD`, `SERVER`, and `ORG` variables are correct. Check network connectivity and PCE API availability.
- **Zero Active Syncing Count**: Verify the `Policy Sync Counts` in the output. If no workloads have `policy_sync == "syncing"`, the count will be 0. Inspect the API response for `security_policy_sync_state`.
- **CSV File Issues**: Ensure write permissions for the `CSV_FILE` path (`/tmp/out.csv` by default).
- **Retry Failures**: If the script fails after 50 retries, check the PCE API logs or increase the `Retry-After` default value if the server is slow to respond.

## License
This script is provided as-is, without warranty. Use and modify it according to your needs, ensuring compliance with your Illumio PCE provider’s terms of service.

```

### Key Updates in the README
1. **Overview**: Updated to mention the new counts (`Active Syncing` and `Offline, Will Sync When Online`) and the retry logic changes.
2. **Features**: Added details about the new counts and clarified the retry logic (50 retries using `Retry-After`).
3. **Usage**: Included example output reflecting the new counts and updated summary format.
4. **Notes**: Emphasized the logic for `active_syncing_count` (online, `policy_sync == "syncing"`) and `offline_will_sync_count` (offline, managed, not uninstalled). Noted the retry logic change.
5. **Troubleshooting**: Added guidance for debugging `active_syncing_count` if it’s 0, referencing the `Policy Sync Counts` section.

### Notes
- The README assumes the script is named `pce_workload_status.py` for consistency. Adjust the filename in the usage section if different.
- The example output is illustrative; actual values depend on your PCE API data.
- The README includes security advice (e.g., not hardcoding credentials) and troubleshooting tips for common issues like zero counts.

Please review the README and let me know if you need adjustments, such as a different format, additional sections, or specific details about your environment! If you’re still seeing issues with `active_syncing_count` being 0, consider sharing the `Policy Sync Counts` or relevant console output for further debugging.
