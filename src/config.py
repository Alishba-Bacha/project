import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("sk-abcdef1234567890abcdef1234567890abcdef12")
CHROMA_COLLECTION = "hallucination_detector"