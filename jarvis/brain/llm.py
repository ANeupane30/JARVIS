"""
We are calling API for processing user query. We will be using openrouter api to access the model.
For now we are implementing simple string input using Openrouter API. 

Openrouter API supports following:
1. Basic Usage
2. Reasoning
3. Tool Calling
4. Web Search
5. Error handling


"""

import requests
from decouple import config

OPENROUTER_API_KEY = config('OPENROUTER_API_KEY')

def llm_response(text):
    response = requests.post(
        'https://openrouter.ai/api/v1/responses',
        headers={
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
        },
        json={
            'model': 'openai/o4-mini',
            'input': text,
            'max_output_tokens': 9000,
        }
    )
    return response.json()