import asyncio
import json

# Import the actual tool functions directly from our server file!
from server import load_model, list_entities

async def run_tests():
    print("==============================================")
    print("🚀 STARTING MCP LOCAL TEST SUITE (No Frontend)")
    print("==============================================\n")

    # TEST 1: Valid input
    print("=== TEST CASE: load_model valid ===")
    # (Since the .NET API is offline, this should neatly catch a connection error!)
    res1 = await load_model("gear.step")
    print(f"Result: {json.dumps(res1, indent=2)}\n")

    # TEST 2: Invalid input (empty file)
    print("=== TEST CASE: load_model invalid (empty file path) ===")
    # Note: If the backend was online, we'd expect Person 2's API to return a 400 error here.
    # Our code should catch whatever non-200 or connection error happens.
    res2 = await load_model("")
    print(f"Result: {json.dumps(res2, indent=2)}\n")

    # TEST 3: list_entities / API failure case
    print("=== TEST CASE: list_entities valid (backend down) ===")
    # Again, ensuring that our tool doesn't crash the program when httpx fails.
    res3 = await list_entities()
    print(f"Result: {json.dumps(res3, indent=2)}\n")

    print("==============================================")
    print("✅ TEST SUITE COMPLETE")
    print("==============================================")

if __name__ == "__main__":
    # Tools are async functions under the hood, so we run them using asyncio
    asyncio.run(run_tests())
