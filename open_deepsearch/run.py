import asyncio
from typing import Any
from .deep_research import deep_research, write_final_report
from .feedback import generate_feedback
from .output_manager import OutputManager

output = OutputManager()

def log(*args: Any) -> None:
    output.log(*args)

async def ask_question(query: str) -> str:
    return input(query)

async def run() -> None:
    initial_query = await ask_question('What would you like to research? ')
    breadth = int(await ask_question('Enter research breadth (recommended 2-10, default 4): ') or 4)
    depth = int(await ask_question('Enter research depth (recommended 1-5, default 2): ') or 2)

    log('Creating research plan...')
    follow_up_questions = await generate_feedback(query=initial_query)  # Await the coroutine
    log('\nTo better understand your research needs, please answer these follow-up questions:')

    answers = []
    for question in follow_up_questions:
        answer = await ask_question(f'\n{question}\nYour answer: ')
        answers.append(answer)

    combined_query = f"Initial Query: {initial_query}\nFollow-up Questions and Answers:\n" + \
                     "\n".join([f"Q: {q}\nA: {answers[i]}" for i, q in enumerate(follow_up_questions)])
    log('\nResearching your topic...')
    log('\nStarting research with progress tracking...\n')

    result = await deep_research(query=combined_query, breadth=breadth, depth=depth, on_progress=output.update_progress)
    log(f"\n\nLearnings:\n\n{''.join(result.learnings)}")
    log(f"\n\nVisited URLs ({len(result.visited_urls)}):\n\n{''.join(result.visited_urls)}")
    log('Writing final report...')

    report = await write_final_report(prompt=combined_query, learnings=result.learnings, visited_urls=result.visited_urls)
    with open('output.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n\nFinal Report:\n\n{report}")
    print('\nReport has been saved to output.md')

def main():
    asyncio.run(run())

if __name__ == '__main__':
    asyncio.run(run())