#!/usr/bin/env python3
"""Test script to debug Z.ai API connection."""

import os
import json
import requests

# Check API key
api_key = os.getenv('ZAI_API_KEY')
if not api_key:
    print("❌ ZAI_API_KEY not found in environment")
    print("Set it with: export ZAI_API_KEY=your_key_here")
    exit(1)

print(f"✅ API Key found: {api_key[:10]}...")

# Test API endpoint
url = "https://api.z.ai/api/coding/paas/v4/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "glm-4.6",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello API is working!'"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
}

print(f"\n📡 Testing API at: {url}")
print(f"📤 Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"\n📥 Status Code: {response.status_code}")
    print(f"📥 Headers: {dict(response.headers)}")

    if response.status_code == 200:
        print("\n✅ Success!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"\n❌ Error Response:")
        print(f"Content: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ Request Failed: {e}")