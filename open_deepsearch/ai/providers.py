import os, re
from typing import Any, Dict, List, TypedDict
import openai
import aiohttp
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from dotenv import load_dotenv
import html2text

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

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
FIRECRAWL_KEY = os.getenv('FIRECRAWL_KEY')

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

# Define Search top few number of urls by tavily_client
class TavilySearch:
    def __init__(self):
        self.name = 'tavily.TavilySearch'
        self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

    def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        # Perform search with TAVily API (top results)
        # Extract the string between double quotes
        match = re.search(r'"(.*?)"', query)
        if match:
            query = match.group(1)
        else:
            query = re.sub(r'[*-]', '', query)
        
        search_results = self.tavily_client.search(query, max_results=max_results)
        
        # Extract URLs from search results and filter out google.com results
        urls = [{'url': result["url"], 'title': result["title"]} for result in search_results["results"] if "google.com" not in result["url"]]
        return urls    

# Define WebCrawlerApp
class WebCrawlerApp:
    def __init__(self):
        self.name = 'crawl4ai.AsyncWebCrawler'

    async def crawl_url(self, url: str) -> str:
        try:
            crawler = AsyncWebCrawler(verbose=True)
            # Crawl the URL asynchronously
            result = await crawler.arun(url=url)
            
            # Check if crawl was successful
            if result.success:
                print(f"\nCrawled {url}:")
                print(f"Content (first 200 chars): {result.html[:200]}...")
                
                # Convert HTML to Markdown
                converter = html2text.HTML2Text()
                converter.ignore_links = False  # Set to True to ignore links
                markdown_content = converter.handle(result.html)
                return markdown_content
            else:
                print(f"Failed to crawl {url}: {result.error_message}")
                
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
    

# Define FirecrawlApp
class FirecrawlApp:
    def __init__(self):
        self.api_key = FIRECRAWL_KEY
        #self.api_url = config.get('apiUrl')

    async def crawl_url(self, url: str) -> str:
        app = FirecrawlApp(api_key=self.api_key)
        # Scrape the URL
        scrape_result = app.scrape_url(url, params={'formats': ['markdown']})

        # Check if the scrape was successful
        if scrape_result['success']:
            # Retrieve the markdown content
            markdown_content = scrape_result['data']['markdown']
            # Print the first 500 characters of the markdown content
            print(markdown_content[:500])
            return markdown_content
        else:
            print("Scraping failed:", scrape_result.get('error', 'Unknown error'))
        


# Define SearchResponse
class SearchResponseItem(TypedDict):
    markdown: str
    url: str

class SearchResponse(TypedDict):
    data: List[SearchResponseItem]