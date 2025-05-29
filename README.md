markdown

# PCE Workload Status Script

This Python script retrieves workload information from the Illumio Policy Compute Engine (PCE) API, processes the data, and outputs a detailed status report to both the console and a CSV file. It includes workload states, agent statuses, policy sync states, and summary statistics.

## Features
- Fetches workload data from the PCE API with pagination support.
- Processes workload attributes such as hostname, IP, state, agent status, policy sync, enforcement mode, agent version, health errors, and creation date.
- Outputs formatted workload details to the console.
- Generates a CSV file (`/tmp/out.csv`) with workload details and summary statistics.
- Handles asynchronous API requests and retries for job-based responses.
- Includes error handling for API requests and JSON parsing.

## Prerequisites
- Python 3.6+
- Required Python packages:
  - `requests`
  - `urllib3`
- Access to an Illumio PCE instance with valid API credentials.

## Installation
1. Clone or download the script to your local machine.
2. Install the required Python packages:
   ```bash
   pip install requests

    Ensure you have valid PCE API credentials and the PCE server URL.

Configuration
Modify the following constants at the top of the script to match your PCE environment:

    LOGIN: Your PCE API key ID (e.g., api_1bf4ea537e).
    PASSWD: Your PCE API secret key (e.g., 173e70571d4774d122ddfd777546f7750b0d0454).
    SERVER: The PCE server URL (e.g., https://pce.shocknetwork.com:8443).
    ORG: The organization ID (e.g., 1).
    CSV_FILE: The output CSV file path (default: /tmp/out.csv).

Usage
Run the script from the command line:
bash

python3 pce_workload_status.py

Output

    Console Output: Displays a formatted table of workload details, including:
        Hostname
        IP Address
        State (e.g., online, offline, idle, enforced)
        Agent Status (e.g., active, stopped, uninstalled)
        Policy Sync (e.g., synced, syncing)
        Enforcement Mode
        Status
        Agent Version
        Health Errors
        Managed Since (creation date)
    CSV Output: Saves the same workload details to /tmp/out.csv, along with a summary section that includes:
        State counts
        Agent status counts
        Policy sync counts
    Summary: Printed to the console and appended to the CSV, summarizing the counts of workloads by state, agent status, and policy sync state.

Script Details
Key Functions

    getdata(api_url, auth_creds, base_url): Handles API requests to the PCE, including pagination and asynchronous job processing. Ensures proper URL construction with /api/v2.
    get_workload_state(workload): Determines the workload state (e.g., idle, visibility, enforced, syncing) based on online status, enforcement mode, and agent configuration.
    get_agent_status(workload): Determines the agent status (e.g., active, stopped, offline) based on online status and agent configuration.
    get_workloads(): Asynchronously retrieves all workloads with pagination support.
    fetch_and_display_workloads(): Main function to fetch, process, and output workload data to console and CSV.
    main(): Entry point for async execution.

Error Handling

    Custom APIError exception for API-related errors.
    Handles HTTP errors, JSON decoding issues, and retry logic for asynchronous API jobs.
    Gracefully skips malformed workload entries during processing.

Dependencies

    Uses requests for HTTP requests and urllib3 for SSL handling (disables SSL warnings for simplicity).
    Uses asyncio for asynchronous execution.
    Uses csv for writing output to a CSV file.

Example Output
Console

Total workloads retrieved: 10
Workload Status:
==================================================================================================================
Hostname             IP              State        Agent Status  Policy Sync  Mode         Status       Version     Health Errors    Managed Since
---------------------------------------------------------------------------------------------------------
server1             192.168.1.10    enforced     active        synced       full         running      23.2.0      None            2023-05-01
server2             192.168.1.11    offline      offline       N/A          idle         stopped      N/A         None            2023-04-15
...

Summary:
==================================================
State Counts:
enforced            : 5
offline             : 3
visibility          : 2

Agent Status Counts:
active              : 6
offline             : 3
stopped             : 1

Policy Sync Counts:
synced              : 7
N/A                 : 3

CSV (/tmp/out.csv)
csv

Hostname,IP,State,Agent Status,Policy Sync,Mode,Status,Version,Health Errors,Managed Since
server1,192.168.1.10,enforced,active,synced,full,running,23.2.0,None,2023-05-01
server2,192.168.1.11,offline,offline,N/A,idle,stopped,N/A,None,2023-04-15
...
,,
Summary,,
State,Count
enforced,5
offline,3
visibility,2
,,
Agent Status,Count
active,6
offline,3
stopped,1
,,
Policy Sync,Count
synced,7
N/A,3

Notes

    The script disables SSL verification (verify=False) for simplicity. For production use, enable SSL verification and provide the appropriate certificates.
    Ensure the API credentials have sufficient permissions to access workload data.
    The script assumes the PCE API uses the /api/v2 endpoint structure. Adjust the getdata function if your PCE uses a different API structure.
    The output CSV is overwritten each time the script runs. Back up the file if needed.

Troubleshooting

    API Errors: Check the LOGIN, PASSWD, SERVER, and ORG values for accuracy.
    Connection Issues: Verify network connectivity to the PCE server and ensure the server URL is correct.
    Empty Output: Ensure the API credentials have access to workloads and that the organization ID is valid.
    CSV Issues: Verify write permissions for the /tmp directory or change the CSV_FILE path.

License
This script is provided as-is without any warranty. Use it at your own risk.
Contact
For issues or feature requests, please contact the script maintainer or open an issue in the repository (if applicable).


This README provides a comprehensive overview of the script, including its purpose, setup, usage, output format, and troubleshooting tips, tailored to the provided code. Let me know if you need any adjustments!
