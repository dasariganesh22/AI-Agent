"""
Centralized Google GenAI client instance for IRIS.
Avoids redundant client instantiations and circular import dependencies.
"""
from google import genai
from config import GEMINI_API_KEY

# Single shared Gemini Client instance across the application
client = genai.Client(api_key=GEMINI_API_KEY)
