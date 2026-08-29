import os
import httpx
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_AI_ENDPOINT"),
    api_key=os.getenv("AZURE_AI_API_KEY"),
    api_version="2025-04-01-preview",
    http_client=httpx.Client(
        verify=r"C:\Users\MHussain4\Downloads\nscacert.pem"
    )
)

response = client.chat.completions.create(
    model=os.getenv("AZURE_AI_DEPLOYMENT_NAME"),
    messages=[
        {
            "role": "user",
            "content": "Hello, test Azure AI API."
        }
    ]
)

print(response.choices[0].message.content)