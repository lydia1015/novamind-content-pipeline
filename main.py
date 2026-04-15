"""CLI entry point for the NovaMind AI-Powered Marketing Content Pipeline."""

from __future__ import annotations

import argparse
import sys

from config import PERSONAS, ensure_directories, load_config
from services.content_generator import ContentGenerator
from services.content_optimizer import OPTIMIZATION_OUTPUT_FILE, ContentOptimizer
from services.crm_service import CRMService
from services.metrics_simulator import MetricsSimulator
from services.performance_analyzer import PerformanceAnalyzer


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the NovaMind content pipeline.")
    parser.add_argument(
        "--topic",
        type=str,
        help='Blog topic to generate content for. Example: "AI automation for small creative agencies"',
    )
    return parser.parse_args()


def main() -> int:
    """Run the full content generation, CRM, metrics, and summary workflow."""
    args = parse_args()
    topic = args.topic or input("Enter a blog topic: ").strip()
    if not topic:
        print("A topic is required to run the pipeline.")
        return 1

    ensure_directories()
    config = load_config()

    try:
        content = ContentGenerator(config).generate(topic)
        crm_result = CRMService().run_campaign(content)
        metrics = MetricsSimulator().simulate(topic, crm_result["campaign_entries"])
        summary = PerformanceAnalyzer().analyze(topic, content, metrics)
        ContentOptimizer(config).optimize()
    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        return 1

    print("\nNovaMind AI-Powered Marketing Content Pipeline completed successfully.\n")
    print(f"Topic: {topic}")
    print(f"Blog title: {content['blog_title']}")
    print(f"Personas processed: {', '.join(PERSONAS)}")
    print(f"Campaigns logged: {len(crm_result['campaign_entries'])}")
    print(f"Performance summaries generated: {len(metrics)}")
    print(f"Optimization recommendations generated: {OPTIMIZATION_OUTPUT_FILE}")
    print("\nLatest summary preview:\n")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
