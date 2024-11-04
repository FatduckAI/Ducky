import os

from dotenv import load_dotenv


def get_ollama_client():
    """Returns the base URL for Ollama API hosted on RunPod"""
    load_dotenv()
    RUNPOD_URL = os.getenv('RUNPOD_URL')
    if not RUNPOD_URL:
        raise ValueError("RUNPOD_URL environment variable is not set")
    return RUNPOD_URL.rstrip('/')