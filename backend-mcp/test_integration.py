import httpx
import asyncio
import json

# Import the actual tool functions and variables directly from our server
import server
from server import load_model, list_entities

def print_result(result):
    """Helper to uniformly format the dictionary output."""
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    # Dump the data strictly to make nested JSON look pretty
    print(f"Data: {json.dumps(result.get('data', {}), indent=2)}")
    print("-" * 50 + "\n")

async def run_integration_tests():
    print("=============================================================")
    print("🚀 STARTING MCP + BACKEND INTEGRATION TEST")
    print("=============================================================\n")
    
    # ---------------------------------------------------------
    # 1. DIRECT BACKEND TESTS (Bypass MCP entirely)
    # ---------------------------------------------------------
    print("=== BACKEND DIRECT TEST: GET /api/cad/list_entities ===")
    try:
        # httpx exposes synchronous requests too! (No async needed here)
        r = httpx.get(f"{server.CAD_API_BASE_URL}/api/cad/list_entities", timeout=2.0)
        print(f"Response Code: {r.status_code}")
        print(f"Response Body: {r.text}\n")
    except Exception as e:
        print(f"Backend completely unreachable! Exception: {e}\n")

    print("=== BACKEND DIRECT TEST: POST /api/cad/load_model ===")
    try:
        r = httpx.post(
            f"{server.CAD_API_BASE_URL}/api/cad/load_model", 
            json={"filePath": "sample.step"}, 
            timeout=2.0
        )
        print(f"Response Code: {r.status_code}")
        print(f"Response Body: {r.text}\n")
    except Exception as e:
        print(f"Backend completely unreachable! Exception: {e}\n")
        
    print("=============================================================")
    print("🚀 STARTING NATIVE MCP TOOL TESTS")
    print("=============================================================\n")

    # ---------------------------------------------------------
    # 2. MCP TESTS (Valid Case)
    # ---------------------------------------------------------
    print("=== TEST CASE: MCP list_entities (Valid case) ===")
    res1 = await list_entities()
    print_result(res1)
    
    print("=== TEST CASE: MCP load_model (Valid case) ===")
    res2 = await load_model("sample.step")
    print_result(res2)

    # ---------------------------------------------------------
    # 3. MCP TESTS (Invalid Case - Empty string)
    # ---------------------------------------------------------
    print("=== TEST CASE: MCP load_model (Invalid Case - empty path) ===")
    # Notice we pass "" so Person 2's backend can reject it (usually via 400 Bad Request)
    res3 = await load_model("")
    print_result(res3)

    # ---------------------------------------------------------
    # 4. MCP TESTS (Failure Case - simulate backend down)
    # ---------------------------------------------------------
    print("=== TEST CASE: MCP load_model (Failure Case - Backend Down) ===")
    # Temporarily corrupt the base URL via Python code to force a network timeout/refused.
    # This proves the MCP tool catches and formats network level deaths safely!
    original_url = server.CAD_API_BASE_URL
    server.CAD_API_BASE_URL = "http://172.168.0.6:5001" 
    
    res4 = await load_model("sample.step")
    print_result(res4)
    
    # Restore the actual URL
    server.CAD_API_BASE_URL = original_url
    
    print("=============================================================")
    print("✅ INTEGRATION TEST SUITE COMPLETE")
    print("=============================================================")

if __name__ == "__main__":
    # We use a single asyncio.run() to keep it totally clean since 
    # the server.py methods are defined as purely async functions.
    asyncio.run(run_integration_tests())
