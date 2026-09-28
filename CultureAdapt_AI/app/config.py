import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
IMAGE_MODE = os.getenv("IMAGE_MODE", "mock")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-2.5-flash")
