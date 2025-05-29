#!/usr/bin/env python3

import requests
import json
import time
import os
import sys, csv, asyncio
import re
from typing import List, Dict, Any
from collections import defaultdict
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()

LOGIN = "api_1bf4ed8a2a537e"
PASSWD = "173e70571d425fe5a4cd3a81b2f774d122ddfd777546f7750b0d0454"
SERVER = "https://pce.shocknetwork.com:8443"
ORG = "1"
CSV_FILE = "/tmp/out.csv"


class APIError(Exception):
    """Custom exception for API errors."""
    pass

def getdata(api_url: str, auth_creds: HTTPBasicAuth, base_url: str) -> Any:
    """
    Handles asynchronous requests to the PCE API, properly constructing URLs with /api/v2.
    """
    headers = {'Accept': 'application/json', 'Prefer': 'respond-async'}
    try:
        # Ensure the initial API URL includes /api/v2 if it's not already there
        if not api_url.startswith(f"{base_url}/api/v2"):
            if not api_url.startswith(base_url):
                api_url = f"{base_url}/api/v2{api_url}" if not api_url.startswith('/') else f"{base_url}/api/v2{api_url}"
            else:
                # If it starts with base_url but doesn't have /api/v2, insert it
                api_url = api_url.replace(base_url, f"{base_url}/api/v2", 1)

        r = requests.get(api_url, headers=headers, auth=auth_creds, verify=False)
        r.raise_for_status()
        
        if r.status_code == 202:
            print('Waiting for the PCE to process the request')
            location_header = r.headers.get('Location')
            
            # Properly construct the location URL
            if location_header:
                # Ensure the location URL is absolute
                if not location_header.startswith('http'):
                    # Handle both cases where Location might start with /api/v2 or not
                    if location_header.startswith('/api/v2'):
                        location_url = f"{base_url}{location_header}"
                    else:
                        location_url = f"{base_url}/api/v2{location_header}"
                else:
                    location_url = location_header
                
                print(f"Debug: Checking job status at: {location_url}")
                
                wait_time = int(r.headers.get('Retry-After', 1))
                time.sleep(1)
                headers = {'Accept': 'application/json'}
                retry = 0
                max_retries = 5
                
                while retry < max_retries:
                    try:
                        status_response = requests.get(location_url, headers=headers, auth=auth_creds, verify=False)
                        status_response.raise_for_status()
                        job_status = status_response.json()
                        
                        if job_status.get('status') == 'done':
                            result_href = job_status.get('result', {}).get('href', '')
                            if result_href:
                                # Ensure the result URL is properly constructed
                                if result_href.startswith('/api/v2'):
                                    result_url = f"{base_url}{result_href}"
                                else:
                                    result_url = f"{base_url}/api/v2{result_href}"
                                result_response = requests.get(result_url, headers=headers, auth=auth_creds, verify=False)
                                result_response.raise_for_status()
                                return result_response.json()
                        else:
                            print(f"Job status: {job_status.get('status')}, retrying in {wait_time} seconds (attempt {retry + 1}/{max_retries}).")
                            time.sleep(wait_time)
                            retry += 1
                            
                    except requests.exceptions.RequestException as e:
                        print(f"Error checking job status (attempt {retry + 1}/{max_retries}): {e}")
                        time.sleep(wait_time)
                        retry += 1
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON response for job status.")
                        time.sleep(wait_time)
                        retry += 1
                
                print('\nFailed to retrieve job result after multiple retries.\n')
                return None
            else:
                print('No Location header in 202 response')
                return None
        else:
            return r.json()
            
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response.")
        return None

def get_workload_state(workload: Dict[str, Any]) -> str:
    """Determine the state of a workload."""
    if not workload.get('online', False):
        return "offline"

    if not workload.get('managed', True):
        return "unmanaged"

    agent = workload.get('agent', {})
    agent_status = agent.get('status', '')
    if isinstance(agent_status, dict):
        agent_status = agent_status.get('status', 'unknown').lower()
    elif isinstance(agent_status, str):
        agent_status = agent_status.lower()
    else:
        agent_status = 'unknown'

    if agent_status == 'uninstalled':
        return "uninstalled"

    enforcement = workload.get('enforcement_mode', 'unknown')
    if isinstance(enforcement, dict):
        enforcement = enforcement.get('name', 'unknown').lower()
    elif isinstance(enforcement, str):
        enforcement = enforcement.lower()
    else:
        enforcement = 'unknown'

    config_sync = agent.get('config_sync_state', 'unknown').lower() if isinstance(agent.get('config_sync_state'), str) else 'unknown'

    if enforcement == 'idle':
        state = "idle"
    elif enforcement == 'visibility_only':
        state = "visibility"
    elif enforcement == 'full':
        state = "enforced"
    else:
        state = "active"

    if config_sync == 'syncing':
        state += "/syncing"

    return state

def get_agent_status(workload: Dict[str, Any]) -> str:
    """Determine the agent status."""
    if not workload.get('online', False):
        return "offline"

    agent = workload.get('agent', {})
    agent_status = agent.get('status', '')
    if isinstance(agent_status, dict):
        agent_status = agent_status.get('status', 'unknown').lower()
    elif isinstance(agent_status, str):
        agent_status = agent_status.lower()
    else:
        agent_status = 'unknown'

    config_sync = agent.get('config_sync_state', 'unknown').lower() if isinstance(agent.get('config_sync_state'), str) else 'unknown'

    if agent_status == 'uninstalled':
        return "uninstalled"
    elif agent_status == 'stopped':
        return "stopped"
    elif agent_status in ('running', 'active'):
        return "active/syncing" if config_sync == 'syncing' else "active"
    else:
        return "unknown"

async def get_workloads() -> List[Dict[str, Any]]:
    """Retrieve all workloads from the PCE API with pagination."""
    api_url = f"/orgs/{ORG}/workloads"
    all_workloads = []
    auth = HTTPBasicAuth(LOGIN, PASSWD)

    next_page_url = api_url
    base_url = SERVER

    while next_page_url:
        # Construct full URL with proper /api/v2 prefix
        if not next_page_url.startswith('http'):
            if not next_page_url.startswith('/api/v2'):
                next_page_url = f"/api/v2{next_page_url}" if not next_page_url.startswith('/') else f"/api/v2{next_page_url}"
            full_url = f"{base_url}{next_page_url}"
        else:
            full_url = next_page_url

        workload_data = await asyncio.to_thread(getdata, full_url, auth, base_url)
        if workload_data is None:
            break

        if isinstance(workload_data, list):
            all_workloads.extend(workload_data)
            next_page_url = None
        elif isinstance(workload_data, dict):
            if 'results' in workload_data:
                all_workloads.extend(workload_data['results'])
                next_page = workload_data.get('pagination', {}).get('next')
                if next_page:
                    next_page_url = next_page
                else:
                    next_page_url = None
            else:
                all_workloads.append(workload_data)
                next_page_url = None

        print(f"Retrieved {len(all_workloads)} workloads so far...")

    return all_workloads

async def fetch_and_display_workloads():
    """Fetch workloads asynchronously, display, and write to CSV with summary."""
    try:
        workloads = await get_workloads()

        if not workloads:
            print("No workloads found.")
            return

        print(f"Total workloads retrieved: {len(workloads)}")

        # Initialize counters for summary
        state_counts = defaultdict(int)
        agent_status_counts = defaultdict(int)
        policy_sync_counts = defaultdict(int)

        # Prepare CSV file
        headers = [
            "Hostname", "IP", "State", "Agent Status", "Policy Sync",
            "Mode", "Status", "Version", "Health Errors", "Managed Since"
        ]
        with open(CSV_FILE, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            print("\nWorkload Status:")
            print("=" * 130)
            print(f"{'Hostname':<20} {'IP':<15} {'State':<12} {'Agent Status':<12} {'Policy Sync':<12} {'Mode':<12} {'Status':<12} {'Version':<10} {'Health Errors':<15} {'Managed Since':<15}")
            print("-" * 130)

            for wl in workloads:
                try:
                    hostname = wl.get("hostname", "N/A")[:20]
                    interfaces = wl.get('interfaces') or []
                    ip = next((i.get('address') for i in interfaces if i and i.get('address')), "N/A")
                    state = get_workload_state(wl)
                    agent_status = get_agent_status(wl)

                    agent = wl.get('agent', {})
                    policy_sync = agent.get('status', {}).get('security_policy_sync_state', 'N/A')
                    policy_sync = policy_sync.lower()[:12] if isinstance(policy_sync, str) else str(policy_sync)[:12]

                    mode = wl.get('enforcement_mode', 'N/A')
                    mode = mode.get('name', 'N/A')[:12] if isinstance(mode, dict) else str(mode)[:12]

                    status = agent.get('status', {})
                    status = status.get('status', 'N/A')[:12] if isinstance(status, dict) else str(status)[:12]

                    version = agent.get('status', {}).get('agent_version', 'N/A')[:10]

                    health_errors = agent.get('status', {}).get('agent_health_errors', 'N/A')
                    if isinstance(health_errors, dict):
                        errors = health_errors.get('errors', [])
                        warnings = health_errors.get('warnings', [])
                        health_errors = ','.join(str(e) for e in errors + warnings)[:15] if errors or warnings else 'None'
                    else:
                        health_errors = str(health_errors)[:15]
                    
                    # Get managed_since timestamp
                    managed_since = wl.get('created_at', 'N/A')
                    if managed_since != 'N/A':
                        # Convert timestamp to readable date
                        try:
                            managed_since = time.strftime('%Y-%m-%d', time.localtime(int(managed_since)))
                        except (ValueError, TypeError):
                            pass

                    # Update counters
                    state_counts[state] += 1
                    agent_status_counts[agent_status] += 1
                    policy_sync_counts[policy_sync] += 1

                    # Print to console
                    print(f"{hostname:<20} {ip:<15} {state:<12} {agent_status:<12} {policy_sync:<12} {mode:<12} {status:<12} {version:<10} {health_errors:<15} {managed_since:<15}")

                    # Write to CSV
                    writer.writerow([
                        hostname, ip, state, agent_status, policy_sync,
                        mode, status, version, health_errors, managed_since
                    ])

                except Exception as e:
                    print(f"Error processing workload {wl.get('hostname', 'N/A')}: {str(e)}")
                    continue

            # Write summary to CSV
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["State", "Count"])
            for state, count in sorted(state_counts.items()):
                writer.writerow([state, count])
            writer.writerow([])
            writer.writerow(["Agent Status", "Count"])
            for status, count in sorted(agent_status_counts.items()):
                writer.writerow([status, count])
            writer.writerow([])
            writer.writerow(["Policy Sync", "Count"])
            for sync, count in sorted(policy_sync_counts.items()):
                writer.writerow([sync, count])

        # Print summary to console
        print("\nSummary:")
        print("=" * 50)
        print("State Counts:")
        for state, count in sorted(state_counts.items()):
            print(f"{state:<20}: {count}")
        print("\nAgent Status Counts:")
        for status, count in sorted(agent_status_counts.items()):
            print(f"{status:<20}: {count}")
        print("\nPolicy Sync Counts:")
        for sync, count in sorted(policy_sync_counts.items()):
            print(f"{sync:<20}: {count}")

    except Exception as e:
        print(f"Unexpected error: {str(e)}")

async def main():
    """Main entry point for async execution."""
    await fetch_and_display_workloads()

if __name__ == "__main__":
    asyncio.run(main())