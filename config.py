import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not OPENAI_API_KEY and not GOOGLE_API_KEY:
    raise ValueError("No LLM provider API key found. Please set at least one of OPENAI_API_KEY or GOOGLE_API_KEY in your .env file.")