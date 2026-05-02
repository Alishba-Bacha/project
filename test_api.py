"""
test_api_simple.py
Simple test for the API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_chat():
    print("\nTesting Chat Endpoint...")
    payload = {
        "message": "Does fine-tuning reduce hallucinations in medical papers?",
        "thread_id": "test-001"
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Thread ID: {result.get('thread_id')}")
        print(f"Status: {result.get('status')}")
        print(f"Tools Used: {result.get('tools_used', [])}")
        print(f"Processing Time: {result.get('processing_time', 0):.2f}s")
        print(f"Response Preview: {result.get('message', '')[:200]}...")
    return response.status_code == 200

if __name__ == "__main__":
    print("="*50)
    print("Testing Hallucination Detector API")
    print("="*50)
    
    test_health()
    test_chat()
    
    print("\n✅ Tests completed!")