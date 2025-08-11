import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

models = genai.list_models()

print("Available models:")
for model in models:
    print(f"- {model.name} (supported methods: {model.supported_generation_methods})")
