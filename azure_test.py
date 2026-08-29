import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # reads .env from current directory

endpoint = os.getenv("AZURE_AI_ENDPOINT").rstrip("/")
api_key = os.getenv("AZURE_AI_API_KEY")
deployment = os.getenv("AZURE_AI_DEPLOYMENT_NAME")
api_version = "2024-06-01"

url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

headers = {
    "api-key": api_key,
    "Content-Type": "application/json",
}
payload = {
    "messages": [{"role": "user", "content": "Hello"}],
    "max_completion_tokens": 50,
}

print("Endpoint:", endpoint)
print("Deployment:", deployment)
print("Key length:", len(api_key) if api_key else 0)


try:
    r = httpx.post(url, headers=headers, json=payload, timeout=30)
    print("Status:", r.status_code)
    print(r.text)
except Exception as e:
    print("❌ httpx failed:", type(e).__name__, e)