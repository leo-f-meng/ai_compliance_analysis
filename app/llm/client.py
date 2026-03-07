import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
MODEL = os.getenv("OPEN_AI_MODEL", "gpt-5-nano")
