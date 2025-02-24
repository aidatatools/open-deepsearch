import re
import asyncio
from typing import List, Dict, Optional, Any
from PyPDF2 import PdfFileReader
from io import BytesIO
from pydantic import BaseModel

from open_deepsearch.feedback import generate_object
from .research_progress_results import ResearchProgress, ResearchResult
from .prompt import system_prompt
from .output_manager import OutputManager
from .ai.providers import  custom_model, trim_prompt, WebFirecrawlApp, WebCrawlerApp, TavilySearch, SearchResponse

output = OutputManager()

def log(*args: Any) -> None:
    output.log(*args)

ConcurrencyLimit = 1

#crawler = WebCrawlerApp()
crawler = WebFirecrawlApp()

#searchclient = TavilySearch()

class SerpQuerySchema(BaseModel):
    queries: List[Dict[str, str]]

class SerpResultSchema(BaseModel):
    learnings: List[str]
    followUpQuestions: List[str]

async def generate_serp_queries(query: str, num_queries: int = 3, learnings: Optional[List[str]] = None) -> List[Dict[str, str]]:
    res = await generate_object({
        'model': custom_model,
        'system': system_prompt(),
        'prompt': f"""Given the following prompt from the user, generate a list of SERP queries to research the topic. Return a maximum of {num_queries} queries, but feel free to return less if the original prompt is clear. Make sure each query is unique and not similar to each other: <prompt>{query}</prompt>\n\n""" + (f"Here are some learnings from previous research, use them to generate more specific queries: {'\n'.join(learnings)}" if learnings else ""),
        'schema': SerpQuerySchema
    })
    # Separate queries that start with a number followed by a period
    filtered_queries = [query for query in res['object']['queries'] if re.match(r'^\d+\.', query)]
    research_goals = [goals for goals in res['object']['researchGoal'] if goals.startswith('  ')]

    ans = {}
    ans['object'] = {}
    ans['object']['queries'] = filtered_queries[:num_queries]
    ans['object']['researchGoal'] = research_goals[:num_queries]
    
    log(f"Created {len(ans['object']['queries'])} queries", ans['object']['queries'])
    log(f"Created {len(ans['object']['researchGoal'])} research goals", ans['object']['researchGoal'])
    
    return ans['object']

async def process_serp_result(query: str, result: SearchResponse, num_learnings: int = 3, num_follow_up_questions: int = 3) -> Dict[str, List[str]]:
    contents = [trim_prompt(item['markdown'], 25000) for item in result['data'] if item['markdown']]
    log(f"Ran {query}, found {len(contents)} contents")

    res = await generate_object({
        'model': custom_model,
        'abortSignal': asyncio.TimeoutError(60),
        'system': system_prompt(),
        'prompt': f"""Given the following contents from a SERP search for the query <query>{query}</query>, generate a list of learnings from the contents. Return a maximum of {num_learnings} learnings, but feel free to return less if the contents are clear. Make sure each learning is unique and not similar to each other. The learnings should be concise and to the point, as detailed and information dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any exact metrics, numbers, or dates. The learnings will be used to research the topic further.\n\n<contents>{''.join([f'<content>\n{content}\n</content>' for content in contents])}</contents>""",
        'schema': SerpResultSchema
    }, is_getting_queries=False)
    #log(f"Created {len(res['object']['learnings'])} learnings", res['object']['learnings'])
    return res['object']

async def write_final_report(prompt: str, learnings: List[str], visited_urls: List[str]) -> str:
    learnings_string = trim_prompt(''.join([f'<learning>\n{learning}\n</learning>' for learning in learnings]), 150000)
    res = await generate_object({
        'model': custom_model,
        'system': system_prompt(),
        'prompt': f"""Please write a final report on the topic using the learnings from research. ALL the learnings from research is below : {learnings_string}""",
        'schema': BaseModel
    },is_getting_queries=False, is_final_report=True)

    urls_section = f"\n\n## Sources\n\n{''.join([f'- <{url}>\n' for url in visited_urls])}"
    return (res['object']['content']) + urls_section

async def process_serp_query(serp_query: Dict[str, str], breadth: int, depth: int, learnings: List[str], visited_urls: List[str], progress: ResearchProgress, report_progress: callable) -> Dict[str, List[str]]:
    try:
        # Extract the query between double quotes
        match = re.search(r'"([^"]*)"', serp_query['query'])
        if match:
            extracted_query = match.group(1)
            
        else:
            extracted_query = serp_query['query']

        log(f"Searching for query: {extracted_query}")
        result = crawler.search(extracted_query, max_results=depth)
        log(f"Search results: {result}")
        new_urls = result['urls']
        log(f"New URLs: {new_urls}")

        markdown_results=[]
        for url in new_urls:

            if url.endswith('.pdf'):               
                response = requests.get(url)
                pdf_content = BytesIO(response.content)
                pdf_reader = PdfFileReader(pdf_content)
                text = ""
                for page_num in range(pdf_reader.getNumPages()):
                    text += pdf_reader.getPage(page_num).extract_text()
                markdown_results.append({'markdown': text, 'url': url})
                visited_urls.append(url)  
                
            else:
                markdown_content = await crawler.crawl_url(url)
                markdown_results.append({'markdown': markdown_content, 'url': url})
                visited_urls.append(url) 
                           

        new_breadth = (breadth + 1) // 2
        new_depth = depth - 1
        new_learnings = await process_serp_result(query=serp_query['query'], result={'data': markdown_results}, num_follow_up_questions=new_breadth)
        all_learnings = learnings + new_learnings['learnings']
        all_urls = visited_urls + new_urls

        if new_depth > 0:

            log(f"Researching deeper, breadth: {new_breadth}, depth: {new_depth}")
            report_progress({'current_depth': new_depth, 'current_breadth': new_breadth, 'completed_queries': progress.completed_queries + 1, 'current_query': serp_query['query']})
            next_query = f"Previous research goal: {serp_query['researchGoal']}\nFollow-up research directions: {''.join([f'\n{q}' for q in new_learnings['followUpQuestions']])}".strip()
            recursive_result = await deep_research(query=next_query, breadth=new_breadth, depth=new_depth, learnings=all_learnings, visited_urls=all_urls, on_progress=report_progress)
            return {'learnings': recursive_result.learnings, 'visited_urls': recursive_result.visited_urls}  
            
        else:
            report_progress({'current_depth': 0, 'completed_queries': progress.completed_queries + 1, 'current_query': serp_query['query']})
            return {'learnings': all_learnings, 'visited_urls': all_urls}
    except Exception as e:
        if 'Timeout' in str(e):
            log(f"Timeout error running query: {serp_query['query']}: ", e)
        else:
            log(f"Error running query: {serp_query['query']}: ", e)
        return {'learnings': [], 'visited_urls': []}
    
async def process_serp_query_wrapper(serp_query, breadth, depth, learnings, visited_urls, progress, report_progress):
    return await process_serp_query(serp_query, breadth, depth, learnings, visited_urls, progress, report_progress)

async def deep_research(query: str, breadth: int, depth: int, learnings: Optional[List[str]] = None, visited_urls: Optional[List[str]] = None, on_progress: Optional[callable] = None) -> ResearchResult:
    learnings = learnings or []
    visited_urls = visited_urls or []
    progress = ResearchProgress(current_depth=depth, total_depth=depth, current_breadth=breadth, total_breadth=breadth, total_queries=0, completed_queries=0)
    
    def report_progress(update: Dict[str, Any]) -> None:
        print("report_progress called with:", update, "type:", type(update))  # Add type information
        try:
            if not isinstance(update, dict):
                print(f"Warning: update is not a dictionary, it is {type(update)}")
                return
                
            for key, value in update.items():
                if not hasattr(progress, key):
                    print(f"Warning: progress object has no attribute '{key}'")
                    continue
                setattr(progress, key, value)
        except Exception as e:
            print(f"Error in report_progress: {str(e)}")
            print(f"Update object: {update}")
            print(f"Progress object attributes: {dir(progress)}")

        if on_progress:
            on_progress(progress)

    serp_queries = await generate_serp_queries(query=query, learnings=learnings, num_queries=breadth)
    report_progress({'total_queries': len(serp_queries['queries']), 'current_query': serp_queries['queries'][0] if serp_queries else None})

    tasks = [
        process_serp_query_wrapper({'query':serp_query, 'researchGoal':serp_queries.get('researchGoal', '')[idx] if serp_queries.get('researchGoal') else ''}, breadth, depth, learnings, visited_urls, progress, report_progress)
        for idx, serp_query in enumerate(serp_queries['queries'])
    ]

    results = await asyncio.gather(*tasks)

    all_learnings = list(set(learnings + [learning for result in results for learning in result['learnings']]))
    all_visited_urls = list(set(visited_urls + [url for result in results for url in result['visited_urls']]))  # Ensure unique URLs
    return ResearchResult(learnings=all_learnings, visited_urls=all_visited_urls)
