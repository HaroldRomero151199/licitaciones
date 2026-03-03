import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
SOLR_URL = os.getenv("SOLR_URL")
# Fallback to constructing generic URL if SOLR_URL is not set but base/core are
if not SOLR_URL and os.getenv("SOLR_BASE_URL") and os.getenv("SOLR_CORE"):
    base = os.getenv("SOLR_BASE_URL").rstrip('/')
    core = os.getenv("SOLR_CORE")
    SOLR_URL = f"{base}/{core}"

SOLR_USER = os.getenv("SOLR_USER") or os.getenv("SOLR_USERNAME")
SOLR_PASSWORD = os.getenv("SOLR_PASSWORD")

BATCH_SIZE = 500

if not SOLR_URL:
    raise ValueError("SOLR_URL (or SOLR_BASE_URL and SOLR_CORE) must be set in environment variables.")

if not SOLR_USER or not SOLR_PASSWORD:
    print("Warning: SOLR_USER/SOLR_USERNAME or SOLR_PASSWORD not set. Authentication might fail.")

async def fetch_batch(client, cursor_mark="*"):
    """
    Fetches a batch of documents from Solr using cursorMark.
    """
    params = {
        "q": "*:*",
        "fl": "*",
        "sort": "id asc",
        "rows": BATCH_SIZE,
        "cursorMark": cursor_mark
    }
    
    try:
        response = await client.get(f"{SOLR_URL}/select", params=params)
        response.raise_for_status()
        data = response.json()
        
        docs = data.get("response", {}).get("docs", [])
        next_cursor_mark = data.get("nextCursorMark")
        
        return docs, next_cursor_mark
    except httpx.HTTPError as e:
        print(f"Error fetching batch with cursor {cursor_mark}: {e}")
        raise

async def send_batch(client, docs):
    """
    Sends a batch of documents to Solr for processing/indexing.
    Removes internal fields _version_ and _root_ before sending.
    """
    if not docs:
        return

    # Clean documents
    cleaned_docs = []
    for doc in docs:
        # Remove internal fields
        doc.pop("_version_", None)
        doc.pop("_root_", None)
        cleaned_docs.append(doc)
    
    # Solr update endpoint expects a list of docs directly or wrapped in a command
    # Using JSON update handler
    
    try:
        # commit=false for batch processing
        response = await client.post(
            f"{SOLR_URL}/update",
            params={"commit": "false"},
            json=cleaned_docs
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f"Error sending batch of {len(docs)} docs: {e}")
        # Optionally print response text for debugging
        # print(e.response.text)
        raise

async def commit(client):
    """
    Performs a final commit to Solr.
    """
    try:
        # Send empty json to ensure Content-Type: application/json is set
        response = await client.post(
            f"{SOLR_URL}/update",
            params={"commit": "true"},
            json={}
        )
        response.raise_for_status()
        print("Final commit executed successfully.")
    except httpx.HTTPError as e:
        print(f"Error during final commit: {e}")
        raise

async def main():
    print(f"Starting in-place reindex for {SOLR_URL}")
    
    auth = (SOLR_USER, SOLR_PASSWORD) if SOLR_USER and SOLR_PASSWORD else None
    
    # Increase timeout for large operations
    timeout = httpx.Timeout(30.0, connect=10.0, read=30.0)
    
    async with httpx.AsyncClient(auth=auth, timeout=timeout) as client:
        cursor_mark = "*"
        total_processed = 0
        batch_num = 1
        
        while True:
            print(f"Fetching batch {batch_num}...")
            docs, next_cursor_mark = await fetch_batch(client, cursor_mark)
            
            if not docs:
                print("No more documents found.")
                break
                
            print(f"  Processing {len(docs)} documents...", end=" ", flush=True)
            await send_batch(client, docs)
            print("Done.")
            
            total_processed += len(docs)
            print(f"  Total processed so far: {total_processed}")
            
            if cursor_mark == next_cursor_mark:
                print("Cursor mark reached end.")
                break
                
            cursor_mark = next_cursor_mark
            batch_num += 1
            
        print("All batches processed. Committing...")
        await commit(client)
        print("Reindexing complete.")

if __name__ == "__main__":
    asyncio.run(main())
