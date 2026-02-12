import os
import math
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Configuration
SOLR_BASE_URL = os.getenv("SOLR_BASE_URL", "https://app.solr.klipo.org/solr")
# Use exact core name from request or env
CORE_NAME = os.getenv("SOLR_CORE", "tenders")
SOLR_USERNAME = os.getenv("SOLR_USERNAME")
SOLR_PASSWORD = os.getenv("SOLR_PASSWORD")

# Solr endpoint
SOLR_URL = f"{SOLR_BASE_URL.rstrip('/')}/{CORE_NAME}"

# Constants
BATCH_SIZE = 100
TARGET_STATUS_CODE = 5


def get_total_docs() -> int:
    """
    Queries Solr to get the total number of documents.
    Returns:
        int: Total number of documents found.
    """
    url = f"{SOLR_URL}/select"
    params = {
        "q": "*:*",
        "rows": 0,
        "wt": "json"
    }
    
    auth = (SOLR_USERNAME, SOLR_PASSWORD) if SOLR_USERNAME and SOLR_PASSWORD else None
    
    try:
        response = requests.get(url, params=params, auth=auth)
        response.raise_for_status()
        data = response.json()
        return data["response"]["numFound"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching total docs: {e}")
        if e.response:
             print(f"Response: {e.response.text}")
        exit(1)


def fetch_ids(total_docs: int) -> list:
    """
    Fetches all document IDs using pagination.
    
    Args:
        total_docs (int): Total number of documents to fetch.
        
    Returns:
        list: A list of all document IDs.
    """
    all_ids = []
    # We can fetch in larger chunks for IDs since fields are small
    fetch_rows = 500
    pages = math.ceil(total_docs / fetch_rows)
    
    url = f"{SOLR_URL}/select"
    auth = (SOLR_USERNAME, SOLR_PASSWORD) if SOLR_USERNAME and SOLR_PASSWORD else None

    print(f"Fetching {total_docs} IDs in {pages} pages...")

    for page in range(pages):
        start = page * fetch_rows
        params = {
            "q": "*:*",
            "fl": "id",
            "rows": fetch_rows,
            "start": start,
            "wt": "json"
        }
        
        try:
            response = requests.get(url, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()
            docs = data["response"]["docs"]
            
            ids = [doc["id"] for doc in docs]
            all_ids.extend(ids)
            print(f"  Fetched page {page + 1}/{pages} ({len(ids)} ids)")
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching IDs on page {page + 1}: {e}")
            exit(1)
            
    return all_ids


def atomic_update_batch(ids_batch: list):
    """
    Sends an atomic update request for a batch of IDs.
    
    Args:
        ids_batch (list): List of IDs to update.
    """
    url = f"{SOLR_URL}/update"
    auth = (SOLR_USERNAME, SOLR_PASSWORD) if SOLR_USERNAME and SOLR_PASSWORD else None
    
    # Construct payload
    payload = []
    for doc_id in ids_batch:
        doc_update = {
            "id": doc_id,
            "status_code": {"set": TARGET_STATUS_CODE}
        }
        payload.append(doc_update)
        
    headers = {"Content-Type": "application/json"}
    params = {"commitWithin": 1000}  # Soft commit within 1 second

    try:
        response = requests.post(
            url, 
            json=payload, 
            headers=headers, 
            params=params, 
            auth=auth
        )
        response.raise_for_status()
        print(f"  Batch updated successfully ({len(ids_batch)} docs).")
        
    except requests.exceptions.RequestException as e:
        print(f"Error updating batch: {e}")
        if e.response:
             print(f"Response: {e.response.text}")
        # Build resilience: don't exit, just log failure for this batch
        return


def commit_changes():
    """Performs a hard commit to make changes visible immediately."""
    url = f"{SOLR_URL}/update"
    auth = (SOLR_USERNAME, SOLR_PASSWORD) if SOLR_USERNAME and SOLR_PASSWORD else None
    params = {"commit": "true", "wt": "json"}
    
    try:
        print("Committing changes...")
        response = requests.get(url, params=params, auth=auth)
        response.raise_for_status()
        print("Commit successful.")
    except requests.exceptions.RequestException as e:
        print(f"Error during commit: {e}")


def main():
    print("Starting Solr Atomic Update Script")
    print(f"Target Core: {CORE_NAME}")
    print(f"Target URL: {SOLR_URL}")
    
    # 1. Get exact total count
    total_docs = get_total_docs()
    print(f"Total documents found: {total_docs}")
    
    if total_docs == 0:
        print("No documents to update.")
        return

    # 2. Fetch all IDs
    all_ids = fetch_ids(total_docs)
    print(f"Total IDs collected: {len(all_ids)}")
    
    # 3. Update in batches
    total_batches = math.ceil(len(all_ids) / BATCH_SIZE)
    print(f"Starting updates in {total_batches} batches of {BATCH_SIZE}...")
    
    for i in range(0, len(all_ids), BATCH_SIZE):
        batch_ids = all_ids[i : i + BATCH_SIZE]
        atomic_update_batch(batch_ids)
        
    # 4. Final Commit
    commit_changes()
    print("All operations completed.")


if __name__ == "__main__":
    main()
