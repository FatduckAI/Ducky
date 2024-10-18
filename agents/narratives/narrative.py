"""
Schedule:
- 00:00 UTC every day

"""


from datetime import datetime

from lib import sdk
from lib.anthropic import get_anthropic_client
from lib.defillama import Narratives


def analyze_fdv_performance(period: str) -> str:
    data = Narratives.fdv_performance(period)
    prompt = f"Here's some DeFiLlama FDV (Fully Diluted Valuation) performance data for the past {period} days: {data}\n\nPlease provide a concise summary of the key trends and insights from this data, focusing on the top performers and any notable patterns or changes in the DeFi market based on this FDV performance data."

    response = get_anthropic_client().messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    sdk.save_narrative(data,response.content[0].text.strip())
    print('Narrative saved')
  
  
if __name__ == "__main__":
    print(analyze_fdv_performance('7'))