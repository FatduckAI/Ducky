import os

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')

# Initialize Anthropic client
def get_anthropic_client():
    return anthropic.Anthropic(api_key=anthropic_api_key)