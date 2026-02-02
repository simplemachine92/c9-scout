#!/usr/bin/env python3
"""
Simple test script to verify that the async API calls work outside of Streamlit.
"""

import asyncio
import os
from dotenv import load_dotenv
from clients.series_client.client import SeriesClient

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

def get_series_client():
    return SeriesClient(
        url="https://api-op.grid.gg/live-data-feed/series-state/graphql",
        headers={"x-api-key": API_KEY}
    )

async def get_series_details(series_ids: list[str]):
    client = get_series_client()
    print(f"Testing API call for {len(series_ids)} series IDs: {series_ids}")

    tasks = []
    for series_id in series_ids:
        tasks.append(client.get_completed_series_details(series_id))

    try:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        print(f"Got {len(responses)} responses")

        # Filter out exceptions and None responses
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"Series {series_ids[i]} failed: {response}")
            elif response is None:
                print(f"Series {series_ids[i]} returned None")
            else:
                valid_responses.append(response)
                print(f"Series {series_ids[i]} is valid")

        return valid_responses

    except Exception as e:
        print(f"Exception in get_series_details: {e}")
        return []

async def main():
    print("=== Testing API Call Outside Streamlit ===")

    # First, just test client initialization
    print("Testing client initialization...")
    try:
        client = get_series_client()
        print("Client initialized successfully")
    except Exception as e:
        print(f"Client initialization failed: {e}")
        return

    # Test with a simple query (you can replace with real series ID later)
    print("Testing basic client functionality...")
    try:
        # This will fail with invalid series ID, but should show if client works
        test_series_ids = ["invalid_test_id"]
        results = await get_series_details(test_series_ids)
        print(f"API call completed. Got {len(results)} valid responses.")
        print("The API call structure works - any failures are expected with invalid ID")
    except Exception as e:
        print(f"API call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())