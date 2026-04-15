"""Small orchestration helper for running the NovaMind workflow from the dashboard."""

from __future__ import annotations

import io
from collections import Counter
from contextlib import redirect_stdout

from config import PERSONAS, ensure_directories, load_config
from services.content_generator import ContentGenerator
from services.content_optimizer import ContentOptimizer
from services.crm_service import CRMService
from services.metrics_simulator import MetricsSimulator
from services.performance_analyzer import PerformanceAnalyzer


def run_workflow(topic: str, send_emails: bool = False) -> dict:
    """Run the existing pipeline and return structured results for Streamlit."""
    topic = topic.strip()
    if not topic:
        raise ValueError("A topic is required to run the workflow.")

    ensure_directories()
    config = load_config()

    generation_output = io.StringIO()
    with redirect_stdout(generation_output):
        content = ContentGenerator(config).generate(topic)

    crm_result = CRMService(send_emails=send_emails).run_campaign(content)
    metrics = MetricsSimulator().simulate(topic, crm_result["campaign_entries"])
    summary = PerformanceAnalyzer().analyze(topic, content, metrics)
    recommendations = ContentOptimizer(config).optimize()

    contacts = crm_result.get("contacts", [])
    persona_counts = Counter(contact.get("persona", "Unknown") for contact in contacts)

    return {
        "topic": topic,
        "content": content,
        "crm_result": crm_result,
        "metrics": metrics,
        "summary": summary,
        "recommendations": recommendations,
        "latest_run_timestamp": content.get("generated_at", ""),
        "contact_count": len(contacts),
        "persona_distribution": {persona: persona_counts.get(persona, 0) for persona in PERSONAS},
        "generation_mode": _extract_generation_mode(generation_output.getvalue()),
        "model": config.get("groq_model", "openai/gpt-oss-20b"),
        "crm_provider": "Brevo",
        "send_emails": send_emails,
    }


def _extract_generation_mode(output: str) -> str:
    """Read the generation mode from ContentGenerator's runtime message."""
    if "Content generation mode: Groq" in output:
        return "Groq"
    if "Content generation mode: Local fallback" in output:
        return "Local fallback"
    return "Unknown"
