# open-deepsearch

open-deepsearch ( Deep Research but Open-Sourced )

Q&A for more details, research, and report generation.

## How to install in DEV environment after git clone

```bash
python3 -m venv .venv
source .venv/bin/activate
#modify .env file and put in OPENAI_KEY and FIRECRAWL_KEY
cp .env.example .env
pip install -r requirements.txt
pip install -e .
deepsearch
```

## How to install in PROD environment after pip install open-deepsearch

```bash
python3 -m venv .venv
source .venv/bin/activate
#modify .env file and put in OPENAI_KEY and FIRECRAWL_KEY
cp .env.example .env
pip install open-deepsearch
deepsearch
```

## ⭐ A python port from node.js version

<https://github.com/dzhng/deep-research>

## It only uses OpenAI_KEY and FIRECRAWL_KEY to produce output.md

## Future work

Fix some minor bugs
