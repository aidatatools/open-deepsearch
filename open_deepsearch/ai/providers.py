import os
import re
from typing import Any, Dict, List, TypedDict
import openai
from tiktoken import get_encoding

from .text_splitter import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
load_dotenv()

# Providers
openai.api_key = os.getenv('OPENAI_KEY')
openai.api_base = os.getenv('OPENAI_ENDPOINT', 'https://api.openai.com/v1')

custom_model = os.getenv('OPENAI_MODEL', 'o3-mini')

MIN_CHUNK_SIZE = 140
encoder = get_encoding('o200k_base')

# Trim prompt to maximum context size
def trim_prompt(prompt: str, context_size: int = int(os.getenv('CONTEXT_SIZE', 128000))) -> str:
    if not prompt:
        return ''

    length = len(encoder.encode(prompt))
    if length <= context_size:
        return prompt

    overflow_tokens = length - context_size
    chunk_size = len(prompt) - overflow_tokens * 3
    if chunk_size < MIN_CHUNK_SIZE:
        return prompt[:MIN_CHUNK_SIZE]

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
    trimmed_prompt = splitter.split_text(prompt)[0] if splitter.split_text(prompt) else ''

    if len(trimmed_prompt) == len(prompt):
        return trim_prompt(prompt[:chunk_size], context_size)

    return trim_prompt(trimmed_prompt, context_size)

# Generate object function
async def generate_object(params: Dict[str, Any]) -> Dict[str, Any]:
    response = openai.chat.completions.create(
        model=params['model'],
        messages=[
            {"role": "system", "content": params['system']},
            {"role": "user", "content": params['prompt']}
        ],
        max_tokens=params.get('max_tokens', 1000),
        temperature=params.get('temperature', 0.7),
        top_p=params.get('top_p', 1.0),
        n=params.get('n', 1),
        stop=params.get('stop', None)
    )
    content = response.choices[0].message.content.strip()

    # Split the content by both '\n\n' and '\n  \n'
    questions = re.split(r'\s*\n', content)
    return {'object':{'queries': questions}}
    

# Define FirecrawlApp
class FirecrawlApp:
    def __init__(self, config: Dict[str, str]):
        self.api_key = config.get('apiKey')
        self.api_url = config.get('apiUrl')

    async def search(self, query: str, options: Dict[str, Any]) -> Dict[str, Any]:
        # Implement the search functionality here
        pass

# Define SearchResponse
class SearchResponseItem(TypedDict):
    markdown: str
    url: str

class SearchResponse(TypedDict):
    data: List[SearchResponseItem]