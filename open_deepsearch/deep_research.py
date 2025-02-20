import os
import re
from typing import List, Dict, Optional, Any
from ai.providers import generate_object, custom_model, trim_prompt, FirecrawlApp, SearchResponse
from prompt import system_prompt
from output_manager import OutputManager
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ai.models import ResearchProgress, ResearchResult

from dotenv import load_dotenv
load_dotenv()

output = OutputManager()

def log(*args: Any) -> None:
    output.log(*args)

ConcurrencyLimit = 2

firecrawl = FirecrawlApp({
    'apiKey': os.getenv('FIRECRAWL_KEY', ''),
    'apiUrl': os.getenv('FIRECRAWL_BASE_URL')
})

class SerpQuerySchema(BaseModel):
    queries: List[Dict[str, str]]

class SerpResultSchema(BaseModel):
    learnings: List[str]
    followUpQuestions: List[str]

async def generate_serp_queries(query: str, num_queries: int = 3, learnings: Optional[List[str]] = None) -> List[Dict[str, str]]:
    res = await generate_object({
        'model': custom_model,
        'system': system_prompt(),
        'prompt': f"""Given the following prompt from the user, generate a list of SERP queries to research the topic. Return a maximum of {num_queries} queries, but feel free to return less if the original prompt is clear. Make sure each query is unique and not similar to each other: <prompt>{query}</prompt>/n/n""" + (f"Here are some learnings from previous research, use them to generate more specific queries: {'/n'.join(learnings)}" if learnings else ""),
        'schema': SerpQuerySchema
    })
    log(f"Created {len(res['object']['queries'])} queries", res['object']['queries'])
    return res['object']['queries'][1:1+num_queries]

async def process_serp_result(query: str, result: SearchResponse, num_learnings: int = 3, num_follow_up_questions: int = 3) -> Dict[str, List[str]]:
    contents = [trim_prompt(item['markdown'], 25000) for item in result['data'] if item['markdown']]
    log(f"Ran {query}, found {len(contents)} contents")

    res = await generate_object({
        'model': custom_model,
        'abortSignal': asyncio.TimeoutError(60),
        'system': system_prompt(),
        'prompt': f"""Given the following contents from a SERP search for the query <query>{query}</query>, generate a list of learnings from the contents. Return a maximum of {num_learnings} learnings, but feel free to return less if the contents are clear. Make sure each learning is unique and not similar to each other. The learnings should be concise and to the point, as detailed and information dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any exact metrics, numbers, or dates. The learnings will be used to research the topic further./n/n<contents>{''.join([f'<content>/n{content}/n</content>' for content in contents])}</contents>""",
        'schema': SerpResultSchema
    })
    log(f"Created {len(res['object']['learnings'])} learnings", res['object']['learnings'])
    return res['object']

async def write_final_report(prompt: str, learnings: List[str], visited_urls: List[str]) -> str:
    learnings_string = trim_prompt(''.join([f'<learning>/n{learning}/n</learning>' for learning in learnings]), 150000)
    res = await generate_object({
        'model': custom_model,
        'system': system_prompt(),
        'prompt': f"""Given the following prompt from the user, write a final report on the topic using the learnings from research. Make it as as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:/n/n<prompt>{prompt}</prompt>/n/nHere are all the learnings from previous research:/n/n<learnings>/n{learnings_string}/n</learnings>""",
        'schema': BaseModel
    })
    urls_section = f"/n/n## Sources/n/n{''.join([f'- {url}/n' for url in visited_urls])}"
    return res['object']['reportMarkdown'] + urls_section

async def process_serp_query(serp_query: Dict[str, str], breadth: int, depth: int, learnings: List[str], visited_urls: List[str], progress: ResearchProgress, report_progress: callable) -> Dict[str, List[str]]:
    try:
        result = await firecrawl.search(serp_query['query'], {'timeout': 15000, 'limit': 5, 'scrapeOptions': {'formats': ['markdown']}})
        new_urls = [item['url'] for item in result['data'] if item['url']]
        new_breadth = (breadth + 1) // 2
        new_depth = depth - 1
        new_learnings = await process_serp_result(query=serp_query['query'], result=result, num_follow_up_questions=new_breadth)
        all_learnings = learnings + new_learnings['learnings']
        all_urls = visited_urls + new_urls

        if new_depth > 0:
            log(f"Researching deeper, breadth: {new_breadth}, depth: {new_depth}")
            report_progress({'current_depth': new_depth, 'current_breadth': new_breadth, 'completed_queries': progress.completed_queries + 1, 'current_query': serp_query['query']})
            next_query = f"Previous research goal: {serp_query['researchGoal']}/nFollow-up research directions: {''.join([f'/n{q}' for q in new_learnings['followUpQuestions']])}".strip()
            return await deep_research(query=next_query, breadth=new_breadth, depth=new_depth, learnings=all_learnings, visited_urls=all_urls, on_progress=report_progress)
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
    return await process_serp_query({'query':serp_query}, breadth, depth, learnings, visited_urls, progress, report_progress)

async def deep_research(query: str, breadth: int, depth: int, learnings: Optional[List[str]] = None, visited_urls: Optional[List[str]] = None, on_progress: Optional[callable] = None) -> ResearchResult:
    learnings = learnings or []
    visited_urls = visited_urls or []
    progress = ResearchProgress(current_depth=depth, total_depth=depth, current_breadth=breadth, total_breadth=breadth, total_queries=0, completed_queries=0)

    def report_progress(update: Dict[str, Any]) -> None:
        for key, value in update.items():
            setattr(progress, key, value)
        if on_progress:
            on_progress(progress)

    serp_queries = await generate_serp_queries(query=query, learnings=learnings, num_queries=breadth)
    report_progress({'total_queries': len(serp_queries), 'current_query': serp_queries[0] if serp_queries else None})

    tasks = [
        process_serp_query_wrapper(serp_query, breadth, depth, learnings, visited_urls, progress, report_progress)
        for serp_query in serp_queries
    ]
    results = await asyncio.gather(*tasks)

    all_learnings = list(set([learning for result in results for learning in result['learnings']]))
    all_visited_urls = list(set([url for result in results for url in result['visited_urls']]))
    return ResearchResult(learnings=all_learnings, visited_urls=all_visited_urls)