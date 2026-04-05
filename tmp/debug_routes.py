import httpx
import json

try:
    # 1. Create a box first
    print("Testing generate_shape...")
    r1 = httpx.post("http://localhost:5000/generate_shape", json={
        "command": "generate_shape",
        "name": "test_cube",
        "geometry": {"type": "box", "dimensions": {"width": 10, "height": 10, "depth": 10}}
    })
    print(f"Generate status: {r1.status_code}")
    if r1.status_code == 200:
        res = r1.json()
        print(f"Generated name: {res.get('name')}")
        
    # 2. Try to rotate it
    print("\nTesting rotate_object...")
    r2 = httpx.post("http://localhost:5000/rotate_object", json={
        "object_id": "test_cube",
        "axis": "X",
        "angle": 45
    })
    print(f"Rotate status: {r2.status_code}")
    print(f"Rotate response: {r2.text}")

    # 3. Try to move it
    print("\nTesting move_object...")
    r3 = httpx.post("http://localhost:5000/move_object", json={
        "object_id": "test_cube",
        "x": 10
    })
    print(f"Move status: {r3.status_code}")
    print(f"Move response: {r3.text}")

except Exception as e:
    print(f"Test failed: {e}")
