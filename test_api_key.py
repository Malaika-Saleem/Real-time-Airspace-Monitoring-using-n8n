"""Quick test to verify API key is loading correctly"""
from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv("GROQ_API_KEY", "")
print(f"API Key loaded: {bool(key)}")
print(f"Key length: {len(key) if key else 0}")
print(f"Key starts with: {key[:10] if key else 'N/A'}...")
print(f"Key ends with: ...{key[-10:] if key else 'N/A'}")

