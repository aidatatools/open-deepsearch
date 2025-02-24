from .ai.providers import custom_model
from .prompt import system_prompt
from pydantic import BaseModel
from typing import List
import re
import openai
from typing import Any, Dict, List

class FeedbackSchema(BaseModel):
    questions: List[str]

async def generate_feedback(query: str, num_questions: int = 3) -> List[str]:
    user_feedback = await generate_object({
        'model': custom_model,
        'system': system_prompt(),
        'prompt': f"Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear: <query>{query}</query>",
        'schema': FeedbackSchema
    })
    return user_feedback['object']['queries'][:num_questions] 

async def generate_object(params: Dict[str, Any], is_getting_queries: bool = True, is_final_report: bool = False) -> Dict[str, Any]:
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

    if is_final_report:
        return {'object': {'content': content}}

    # Split the content by both '\n\n' and '\n  \n'
    results = re.split(r'\s*\n', content)
    queries = []
    research_goals = []

    for result in results:
        if re.match(r'^\d+\.', result):
            queries.append(result)
        elif result.startswith('  '):
            research_goals.append(result)

    if is_getting_queries:
        return {'object': {'queries': queries, 'researchGoal': research_goals}}
    else:
        if len(research_goals)==0:
            if len(queries) == 0:
                return {'object': {'learnings': results, 'followUpQuestions': []}}
            else:
                return {'object': {'learnings': queries, 'followUpQuestions': queries}}
        else :
            return {'object': {'learnings': research_goals, 'followUpQuestions': queries}}
        

