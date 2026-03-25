# Agentic Risk Summarizer

An automated multi-agent pipeline that ingests daily financial insurance-risk signals from NewsAPI and RSS feeds, classifies them with Groq LLaMA 3.3, and emails a structured HTML risk summary every morning at 07:00 UTC via GitHub Actions.

## Project Structure

```text
agentic-risk-summarizer/
├── config.py
├── schemas.py
├── pipeline.py
├── delivery.py
├── report_template.html
├── agents/
│   ├── __init__.py
│   ├── fetcher.py
│   ├── classifier.py
│   └── summarizer.py
├── data/
│   ├── rss_feeds.json
│   └── processed_urls.json
├── reports/
│   └── .gitkeep
├── tests/
│   ├── test_fetcher.py
│   ├── test_classifier.py
│   └── test_schemas.py
├── .github/
│   └── workflows/
│       └── daily_pipeline.yml
├── requirements.txt
└── .env.example
```

## Setup

1. Clone and enter the repository.
2. Create a Python 3.11 virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` from `.env.example` and fill values:
   - `GROQ_API_KEY`
   - `NEWS_API_KEY`
   - `GMAIL_USER`
   - `GMAIL_APP_PASSWORD`
   - `RECIPIENT_EMAIL` (optional, defaults to `GMAIL_USER`)

## Run locally

```bash
python pipeline.py
```

Outputs:
- `reports/YYYY-MM-DD.json` archive
- HTML email sent through Gmail SMTP

## GitHub Actions

Workflow file: `.github/workflows/daily_pipeline.yml`

Triggers:
- Daily at `07:00 UTC`
- Manual via `workflow_dispatch`

Required repository secrets:
- `GROQ_API_KEY`
- `NEWS_API_KEY`
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`

## Testing

```bash
python -m unittest discover -s tests -v
```
