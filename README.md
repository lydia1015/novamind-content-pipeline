# NovaMind Content Pipeline

## Overview

This repository contains a submission-ready MVP for the take-home assignment **“AI-Powered Marketing Content Pipeline.”** The project simulates how NovaMind, a fictional AI startup serving small creative agencies, could turn one campaign topic into audience-specific content, route that content through a lightweight CRM workflow, log campaign activity, simulate performance, and generate a short performance summary.

The scope is intentionally simple:

- local Python CLI only
- JSON files for storage
- mocked CRM behavior with HubSpot-inspired endpoints and payloads
- optional Groq-powered generation with a deterministic local fallback

The result is a project that is easy to run, easy to inspect, and complete enough to discuss in an interview.

## Quickstart

### 1. Create a virtual environment

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

Then edit `.env` to include:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Important notes:

- `GROQ_API_KEY` is optional. If it is missing or blank, the app still runs using the built-in fallback content generator.
- No secrets are hardcoded anywhere in the repository.
- `.env` should stay local and should not be committed.

### 4. Run the pipeline

```bash
python3 main.py --topic "AI automation for small creative agencies"
```

You can also run interactively:

```bash
python3 main.py
```

## What The App Does

For a single topic input, the pipeline:

1. Generates a blog title
2. Generates a blog outline
3. Generates a short blog draft of roughly 400 to 600 words
4. Generates three newsletter variants tailored to:
   - Creative Agency Owner
   - Operations Manager at a Small Agency
   - Freelance Creative Professional
5. Stores generated content in `data/generated_content.json`
6. Loads sample contacts from `data/contacts.json`
7. Simulates CRM contact upserts, list membership, segmentation, and campaign assignment
8. Logs campaign metadata to `data/campaign_logs.json`
9. Simulates performance by persona segment and stores it in `data/performance_history.json`
10. Writes a markdown summary to `outputs/latest_run_summary.md`

## Architecture

### Entry Point

- `main.py`
  Coordinates the full pipeline from topic input through summary generation.

### Configuration

- `config.py`
  Centralizes file paths, persona constants, and environment loading.

### Prompt Layer

- `prompts/content_prompts.py`
  Defines the prompt used when Groq generation is enabled.

### Services

- `services/content_generator.py`
  Generates the title, outline, draft, and persona-specific newsletters.
- `services/crm_service.py`
  Simulates HubSpot-style contact sync, segmentation, list assignment, and campaign send logging.
- `services/campaign_logger.py`
  Appends JSON records to campaign and performance history files.
- `services/metrics_simulator.py`
  Produces deterministic mock open, click, and unsubscribe metrics.
- `services/performance_analyzer.py`
  Creates a concise campaign summary and recommendation.

## Folder Structure

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

## Sample Data Files

The repository includes starter data so the project is runnable immediately:

- `data/contacts.json`
  Seed contacts mapped to the three required personas.
- `data/segment_definitions.json`
  Sample CRM segment metadata including HubSpot-style list IDs and segmentation logic notes.
- `data/generated_content.json`
  Latest generated content payload.
- `data/campaign_logs.json`
  Latest mocked campaign send records.
- `data/performance_history.json`
  Latest performance simulation output.

## Tools, APIs, and Model Choices

- **Python 3**
- **Groq API** for optional LLM content generation
- **OpenAI Python SDK** used as a lightweight OpenAI-compatible client for Groq
- **python-dotenv** for local environment loading convenience
- **`openai/gpt-oss-20b`** as the default Groq model value in `.env.example`
- **Local JSON storage** for transparency and easy review

## Assumptions And Mocked Components

- This is a local MVP, not a production system.
- CRM behavior is mocked intentionally to keep the exercise self-contained.
- HubSpot-inspired endpoints and payload shapes are included in `services/crm_service.py` to show where a real integration would be added.
- Performance is simulated deterministically instead of using a random generator so repeated runs are easier to compare.
- If Groq output is unavailable, fallback content is generated locally so the project remains demoable with minimal setup.

## How HubSpot Could Be Connected In A Real Version

The mocked CRM layer could be replaced with real API calls for:

- contact upserts
- static or active list membership
- audience segmentation based on persona properties
- marketing email sends
- campaign response logging

The current structure keeps those boundaries explicit so the mocked workflow can be swapped out incrementally without changing the rest of the pipeline.

## Example Outputs

After running the project, you should expect:

- a generated content payload in `data/generated_content.json`
- campaign logs showing persona-to-newsletter assignment in `data/campaign_logs.json`
- simulated performance by audience segment in `data/performance_history.json`
- a readable markdown summary in `outputs/latest_run_summary.md`

## Exact Commands To Run

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 main.py --topic "AI automation for small creative agencies"
```

If you want to skip Groq and use only the fallback generator, keep `.env` like this:

```env
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
```
