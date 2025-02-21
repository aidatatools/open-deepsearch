from .ai.providers import generate_object, custom_model
from .prompt import system_prompt
from pydantic import BaseModel
from typing import List

class FeedbackSchema(BaseModel):
    questions: List[str]

async def generate_feedback(query: str, num_questions: int = 3) -> List[str]:
    user_feedback = await generate_object({
        'model': custom_model,
        'system': system_prompt(),
        'prompt': f"Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear: <query>{query}</query>",
        'schema': FeedbackSchema
    })
    return user_feedback['object']['queries'][1:1+num_questions] #skip the first question as it is the original query