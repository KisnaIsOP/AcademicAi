from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
loaded = load_dotenv(env_path)
print(f"DEBUG: Loading .env from {env_path}")
print(f"DEBUG: .env loaded: {loaded}")
print(f"DEBUG: API Key present: {bool(os.getenv('OPENROUTER_API_KEY'))}")
if os.getenv('OPENROUTER_API_KEY'):
    print(f"DEBUG: API Key starts with: {os.getenv('OPENROUTER_API_KEY')[:10]}...")

try:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv('OPENROUTER_API_KEY'),
    )
    print("OpenRouter client successfully configured")
except Exception as e:
    print(f"OpenRouter Configuration Error: {e}")
