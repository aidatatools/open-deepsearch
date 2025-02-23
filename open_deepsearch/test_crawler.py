import os, asyncio
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from dotenv import load_dotenv
import html2text

# Load environment variables from .env file
load_dotenv()

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
# Initialize TAVily client
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Define your search query
query = 'dog behavior studies in Taiwan'

# Asynchronous crawling function
async def crawl_url(crawler, url):
    try:
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

            # Save to a Markdown file
            output_file = f"{url.replace('https://', '').replace('/', '_')}.md"
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(markdown_content)

            print(f"Markdown content saved to '{output_file}'")

            # Optional: Extract structured data (e.g., paragraphs) using CSS
            extraction_strategy = JsonCssExtractionStrategy(
                "p", "paragraphs", return_type="list"
            )
            extracted_data = await crawler.aextract(url=url, extraction_strategy=extraction_strategy)
            if extracted_data and "paragraphs" in extracted_data:
                print(f"Extracted paragraphs (first 2):")
                for i, para in enumerate(extracted_data["paragraphs"][:2], 1):
                    print(f"{i}. {para[:100]}...")
        else:
            print(f"Failed to crawl {url}: {result.error_message}")
            
    except Exception as e:
        print(f"Error crawling {url}: {str(e)}")

# Main async function to run the search and crawl
async def main():
    try:
        # Perform search with TAVily API (top 5 results)
        search_results = tavily_client.search(query, max_results=5)
        
        # Extract URLs from search results
        urls = [result["url"] for result in search_results["results"]]
        print("Top URLs found:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")

        # Initialize AsyncWebCrawler
        async with AsyncWebCrawler(verbose=True) as crawler:
            # Warm up the crawler (optional for performance)
            await crawler.awarmup()

            # Crawl all URLs concurrently
            tasks = [crawl_url(crawler, url) for url in urls]
            await asyncio.gather(*tasks)

    except Exception as e:
        print(f"Error during search or crawling: {str(e)}")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())