# open-deepsearch
open-deepsearch ( Deep Research but Open-Sourced )

Q&A for more details, research, and report generation.

## How to install in DEV environment after git clone
```bash
python3 -m venv .venv
source .venv/bin/activate
#modify .env file and put in OPENAI_KEY
cp .env.example .env
pip install -r requirements.txt
pip install -e .
deepsearch
```
⭐ A python port from node.js version
<https://github.com/dzhng/deep-research>

## As for now (2025-02-21, v0.0.3), it only uses OpenAI to produce output.md

## Future work

Try out FIRECRAWL or TAVILY to craw recent web data
