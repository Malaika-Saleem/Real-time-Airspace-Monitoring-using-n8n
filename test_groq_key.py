"""Test Groq API key directly"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("GROQ_API_KEY", "").strip()

if not api_key:
    print("ERROR: GROQ_API_KEY not found in .env")
    exit(1)

print(f"API Key length: {len(api_key)}")
print(f"API Key starts with: {api_key[:10]}...")
print(f"API Key ends with: ...{api_key[-10:]}")

# Test the API key directly with Groq
url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"\nGroq API Test:")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ API Key is VALID!")
        models = response.json()
        print(f"Available models: {len(models.get('data', []))}")
    elif response.status_code == 401:
        print("❌ API Key is INVALID (401 Unauthorized)")
        print(f"Response: {response.text[:200]}")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error testing API key: {e}")

