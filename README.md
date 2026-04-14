# NovaMind Content Pipeline

## Overview

This repository contains a submission-ready MVP for the take-home assignment **“AI-Powered Marketing Content Pipeline.”** It simulates how NovaMind, a fictional AI startup serving small creative agencies, could turn one campaign topic into multi-format content, sync audience contacts into a CRM, send persona-specific newsletters, and generate a simple post-campaign summary.

The implementation is intentionally lightweight:

- local Python CLI
- Groq for content generation
- Brevo for CRM and email delivery
- local JSON files for logs and generated artifacts

## End-to-End Workflow

For a single topic input, the app:

1. Generates a blog title, outline, short blog draft, and three persona-specific newsletter versions using Groq
2. Loads local sample contacts from `data/contacts.json`
3. Creates or updates those contacts in Brevo
4. Maps each contact into the correct persona-based Brevo list
5. Sends the matching newsletter version through Brevo transactional email
6. Logs campaign metadata locally in `data/campaign_logs.json`
7. Simulates performance metrics and stores them in `data/performance_history.json`
8. Writes a markdown summary to `outputs/latest_run_summary.md`

## Tech Stack

- **Python 3**
- **Groq API** for LLM content generation
- **OpenAI Python SDK** as the OpenAI-compatible client for Groq
- **Brevo API** for CRM contact sync and transactional email sending
- **requests** for Brevo API calls
- **python-dotenv** for local environment loading

## Project Structure

```text
novamind-content-pipeline/
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── config.py
├── prompts/
│   ├── __init__.py
│   └── content_prompts.py
├── services/
│   ├── __init__.py
│   ├── campaign_logger.py
│   ├── content_generator.py
│   ├── crm_service.py
│   ├── metrics_simulator.py
│   └── performance_analyzer.py
├── data/
│   ├── contacts.json
│   ├── segment_definitions.json
│   ├── generated_content.json
│   ├── campaign_logs.json
│   └── performance_history.json
└── outputs/
    └── latest_run_summary.md
```

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a local `.env` file

```bash
cp .env.example .env
```

Use this format:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

BREVO_API_KEY=your_brevo_api_key_here
BREVO_SENDER_EMAIL=your_sender_email_here
BREVO_SENDER_NAME=NovaMind
BREVO_LIST_ID_OWNER=123
BREVO_LIST_ID_OPERATIONS=456
BREVO_LIST_ID_FREELANCE=789
```

Notes:

- If `GROQ_API_KEY` is blank, the app falls back to a deterministic local content generator.
- Brevo credentials are required for real CRM sync and transactional email sending.
- No secrets are hardcoded in the repository.

## Run Locally

Run with a topic directly:

```bash
python3 main.py --topic "AI automation for small creative agencies"
```

Or run interactively:

```bash
python3 main.py
```

## Outputs

After a successful run:

- `data/generated_content.json` stores the generated blog and newsletter content
- `data/campaign_logs.json` stores campaign metadata and Brevo send details
- `data/performance_history.json` stores simulated open, click, and unsubscribe metrics
- `outputs/latest_run_summary.md` stores the latest markdown summary

## Assumptions and Demo Notes

- This project is designed as a small demo, not a production system.
- Sample and test contacts were used for safe CRM and email workflow validation.
- Performance metrics are simulated locally so the pipeline always produces a summary, even though CRM sync and email sending use Brevo.
- The structure is intentionally simple so the end-to-end flow is easy to review in a take-home setting.
