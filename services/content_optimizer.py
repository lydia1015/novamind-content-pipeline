"""Generate post-campaign content optimization recommendations."""

from __future__ import annotations

import json
from pathlib import Path

from config import GENERATED_CONTENT_FILE, LATEST_SUMMARY_FILE, OUTPUTS_DIR, PERFORMANCE_HISTORY_FILE, load_config
from prompts.optimization_prompts import build_optimization_prompt


OPTIMIZATION_OUTPUT_FILE = OUTPUTS_DIR / "content_optimization_recommendations.md"


class ContentOptimizer:
    """Use latest campaign artifacts to recommend what to test next."""

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or load_config()
        self.api_key = self.config.get("groq_api_key", "")
        self.model = self.config.get("groq_model", "openai/gpt-oss-20b")

    def optimize(self) -> str:
        """Generate and save content optimization recommendations."""
        generated_content = self._load_json(GENERATED_CONTENT_FILE, {})
        performance_history = self._load_json(PERFORMANCE_HISTORY_FILE, [])
        campaign_summary = self._load_text(LATEST_SUMMARY_FILE)

        if self.api_key:
            recommendations = self._generate_with_groq(generated_content, performance_history, campaign_summary)
        else:
            recommendations = self._generate_fallback(generated_content, performance_history)

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        OPTIMIZATION_OUTPUT_FILE.write_text(recommendations, encoding="utf-8")
        return recommendations

    def _generate_with_groq(self, generated_content: dict, performance_history: list, campaign_summary: str) -> str:
        """Generate recommendations through Groq's OpenAI-compatible API, falling back on errors."""
        try:
            from openai import OpenAI

            optimization_context = self._build_optimization_context(
                generated_content,
                performance_history,
                campaign_summary,
            )
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            response = client.responses.create(
                model=self.model,
                input=build_optimization_prompt(optimization_context),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "novamind_content_optimization",
                        "schema": self._recommendation_schema(),
                        "strict": True,
                    }
                },
            )
            recommendations = json.loads(response.output_text.strip())
            print("Optimization generation mode: Groq")
            return self._render_recommendations(recommendations)
        except Exception as exc:
            print(f"Groq optimization recommendation generation failed: {exc}")
            return self._generate_fallback(generated_content, performance_history)

    def _generate_fallback(self, generated_content: dict, performance_history: list) -> str:
        """Create deterministic recommendations from the latest local performance records."""
        print("Optimization generation mode: Local fallback")
        best_open = self._best_metric(performance_history, "open_rate")
        best_click = self._best_metric(performance_history, "click_rate")
        highest_unsub = self._best_metric(performance_history, "unsubscribe_rate")
        weakest_click = self._weakest_metric(performance_history, "click_rate")

        best_click_features = best_click.get("content_features", {})
        strongest_angle = self._strongest_angle(best_click_features)
        cta_pattern = "clear CTA language" if best_click_features.get("has_cta") else "a more explicit action-oriented CTA"
        needs_specificity = highest_unsub.get("persona", "the highest-risk segment")

        subject_suggestions = self._subject_line_suggestions(generated_content, best_open, best_click)
        persona_revisions = self._persona_revisions(performance_history)

        return (
            "# Content Optimization Recommendations\n\n"
            "## What Worked\n\n"
            f"- **{best_open.get('persona', 'The top open-rate segment')}** had the strongest open-rate signal, so keep the subject-line framing close to what made that segment stop and read.\n"
            f"- **{best_click.get('persona', 'The top click-rate segment')}** drove the strongest click intent, especially around the **{strongest_angle}** angle.\n"
            f"- The next campaign should preserve **{cta_pattern}** where it appears connected to action, not just awareness.\n\n"
            "## What Underperformed\n\n"
            f"- **{weakest_click.get('persona', 'The weakest click-rate segment')}** needs a sharper reason to click, not just a broader automation benefit.\n"
            f"- **{needs_specificity}** should get a more specific value proposition to reduce unsubscribe risk and make the message feel less interchangeable.\n\n"
            "## Likely Reasons\n\n"
            f"- The strongest copy pattern appears to combine **{strongest_angle}** with a concrete operational benefit.\n"
            "- Segments with clearer process or outcome language are more likely to understand the next step quickly.\n"
            "- Generic automation framing is less useful than naming the workflow, handoff, or client-delivery moment being improved.\n\n"
            "## What To Test Next\n\n"
            f"- Test a subject line that pairs the **{strongest_angle}** angle with a specific client-delivery outcome.\n"
            f"- Reuse the **{best_click.get('persona', 'top-click segment')}** CTA pattern in one alternate version for another persona.\n"
            f"- Create one variant for **{needs_specificity}** that names a narrower pain point and a more concrete next action.\n\n"
            "## Next Topic Ideas\n\n"
            "1. How small creative agencies can turn one campaign idea into a repeatable content engine\n"
            "2. The lean agency guide to AI-assisted campaign operations and client reporting\n"
            "3. How freelancers and boutique agencies can repurpose briefs into multi-channel assets faster\n\n"
            "## Headline And Subject Line Ideas\n\n"
            f"- Keep testing the **{strongest_angle}** angle because it showed the strongest engagement signal.\n"
            f"- Reuse **{cta_pattern}** from **{best_click.get('persona', 'the top-click segment')}** in at least one new variant.\n"
            f"- Try: \"{subject_suggestions[0]}\"\n"
            f"- Try: \"{subject_suggestions[1]}\"\n\n"
            "## Persona-Specific Revision Suggestions\n\n"
            f"{persona_revisions}\n\n"
            "## Optimization Memo\n\n"
            f"The next campaign should keep the message pattern that worked best for **{best_click.get('persona', 'the strongest segment')}** "
            f"while tightening the value proposition for **{needs_specificity}**. Prioritize one test that combines a benefit-led subject line "
            "with a clearer CTA, then compare whether workflow-efficiency language or growth-outcome language produces stronger click intent. "
            "This keeps the next iteration focused, measurable, and aligned with NovaMind's small-agency audience."
        )

    def _best_metric(self, records: list, metric_name: str) -> dict:
        """Return the record with the highest metric value."""
        if not records:
            return {}
        return max(records, key=lambda item: float(item.get(metric_name, 0.0)))

    def _build_optimization_context(
        self,
        generated_content: dict,
        performance_history: list,
        campaign_summary: str,
    ) -> dict:
        """Build a compact context package for Groq recommendation generation."""
        best_click = self._best_metric(performance_history, "click_rate")
        best_open = self._best_metric(performance_history, "open_rate")
        weakest_click = self._weakest_metric(performance_history, "click_rate")
        highest_unsub = self._best_metric(performance_history, "unsubscribe_rate")
        newsletters_by_persona = {
            newsletter.get("persona"): newsletter
            for newsletter in generated_content.get("newsletters", [])
            if isinstance(newsletter, dict)
        }

        persona_snapshots = []
        for record in performance_history:
            persona = record.get("persona", "Unknown persona")
            newsletter = newsletters_by_persona.get(persona, {})
            selected_body = newsletter.get("body", "")
            persona_snapshots.append(
                {
                    "persona": persona,
                    "open_rate": self._metric_value(record, "open_rate"),
                    "click_rate": self._metric_value(record, "click_rate"),
                    "unsubscribe_rate": self._metric_value(record, "unsubscribe_rate"),
                    "recipient_count": record.get("recipient_count", record.get("total_contacts", 0)),
                    "selected_subject_line": newsletter.get("subject_line") or record.get("subject_line", ""),
                    "selected_preview_text": newsletter.get("preview_text") or record.get("preview_text", ""),
                    "selected_body_angle": newsletter.get("selected_body_angle", ""),
                    "selected_body_excerpt": selected_body[:450],
                    "subject_line_options": newsletter.get("subject_line_options", []),
                    "preview_text_options": newsletter.get("preview_text_options", []),
                    "content_features": record.get("content_features", {}),
                    "reasoning_notes": record.get("reasoning_notes", []),
                }
            )

        return {
            "topic": generated_content.get("topic", ""),
            "blog_title": generated_content.get("blog_title", ""),
            "campaign_summary": campaign_summary,
            "performance_readout": {
                "best_open_rate_persona": self._persona_metric_summary(best_open),
                "best_click_rate_persona": self._persona_metric_summary(best_click),
                "weakest_click_rate_persona": self._persona_metric_summary(weakest_click),
                "highest_unsubscribe_risk_persona": self._persona_metric_summary(highest_unsub),
            },
            "persona_snapshots": persona_snapshots,
        }

    def _persona_metric_summary(self, record: dict) -> dict:
        """Return a compact persona and metric summary for the optimizer prompt."""
        if not record:
            return {}
        return {
            "persona": record.get("persona", ""),
            "open_rate": self._metric_value(record, "open_rate"),
            "click_rate": self._metric_value(record, "click_rate"),
            "unsubscribe_rate": self._metric_value(record, "unsubscribe_rate"),
            "content_features": record.get("content_features", {}),
        }

    def _weakest_metric(self, records: list, metric_name: str) -> dict:
        """Return the record with the lowest metric value."""
        if not records:
            return {}
        return min(records, key=lambda item: float(item.get(metric_name, 0.0)))

    def _metric_value(self, record: dict, metric_name: str) -> float:
        """Prefer modeled metric values when the simulator provides them."""
        modeled_name = f"modeled_{metric_name}"
        return float(record.get(modeled_name, record.get(metric_name, 0.0)))

    def _render_recommendations(self, recommendations: dict) -> str:
        """Render structured Groq recommendations into the existing markdown output format."""
        topics = recommendations.get("next_topic_suggestions", [])
        headlines = recommendations.get("headline_suggestions", [])
        persona_revisions = recommendations.get("persona_revision_suggestions", [])
        what_worked = recommendations.get("what_worked", [])
        what_underperformed = recommendations.get("what_underperformed", [])
        likely_reasons = recommendations.get("likely_reasons", [])
        tests = recommendations.get("what_to_test_next", [])
        memo = recommendations.get("optimization_memo", "")

        topic_lines = "\n".join(f"{index}. {topic}" for index, topic in enumerate(topics, start=1))
        headline_lines = "\n".join(f"- {headline}" for headline in headlines)
        worked_lines = "\n".join(f"- {item}" for item in what_worked)
        underperformed_lines = "\n".join(f"- {item}" for item in what_underperformed)
        reason_lines = "\n".join(f"- {item}" for item in likely_reasons)
        test_lines = "\n".join(f"- {item}" for item in tests)
        revision_lines = "\n".join(
            f"- **{item.get('persona', 'Unknown persona')}:** {item.get('recommendation', '')}"
            for item in persona_revisions
        )

        return (
            "# Content Optimization Recommendations\n\n"
            "## What Worked\n\n"
            f"{worked_lines}\n\n"
            "## What Underperformed\n\n"
            f"{underperformed_lines}\n\n"
            "## Likely Reasons\n\n"
            f"{reason_lines}\n\n"
            "## What To Test Next\n\n"
            f"{test_lines}\n\n"
            "## Next Topic Ideas\n\n"
            f"{topic_lines}\n\n"
            "## Headline And Subject Line Ideas\n\n"
            f"{headline_lines}\n\n"
            "## Persona-Specific Revision Suggestions\n\n"
            f"{revision_lines}\n\n"
            "## Strategist Memo\n\n"
            f"{memo}"
        )

    def _recommendation_schema(self) -> dict:
        """Return the structured output schema for Groq optimization recommendations."""
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "what_worked",
                "what_underperformed",
                "likely_reasons",
                "what_to_test_next",
                "next_topic_suggestions",
                "headline_suggestions",
                "persona_revision_suggestions",
                "optimization_memo",
            ],
            "properties": {
                "what_worked": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 3,
                    "items": {"type": "string"},
                },
                "what_underperformed": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 2,
                    "items": {"type": "string"},
                },
                "likely_reasons": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 3,
                    "items": {"type": "string"},
                },
                "what_to_test_next": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {"type": "string"},
                },
                "next_topic_suggestions": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {"type": "string"},
                },
                "headline_suggestions": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 3,
                    "items": {"type": "string"},
                },
                "persona_revision_suggestions": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["persona", "recommendation"],
                        "properties": {
                            "persona": {"type": "string"},
                            "recommendation": {"type": "string"},
                        },
                    },
                },
                "optimization_memo": {"type": "string"},
            },
        }

    def _strongest_angle(self, features: dict) -> str:
        """Translate content features into a simple winning angle label."""
        if features.get("emphasizes_workflow_efficiency"):
            return "workflow-efficiency"
        if features.get("emphasizes_growth_outcomes"):
            return "growth-outcome"
        if features.get("persona_fit") == "high":
            return "persona-fit"
        return "practical automation"

    def _subject_line_suggestions(self, generated_content: dict, best_open: dict, best_click: dict) -> list:
        """Create two improved subject line suggestions from observed winning patterns."""
        topic = generated_content.get("topic", "AI automation for small creative agencies")
        click_persona = best_click.get("persona", "small agency teams")
        return [
            f"Turn {topic} into a repeatable agency growth workflow",
            f"What {click_persona} can automate first without slowing client work",
        ]

    def _persona_revisions(self, records: list) -> str:
        """Build concise revision guidance for each persona segment."""
        lines = []
        seen_personas = set()
        for record in records:
            persona = record.get("persona", "Unknown persona")
            if persona in seen_personas:
                continue
            seen_personas.add(persona)
            features = record.get("content_features", {})
            if features.get("emphasizes_workflow_efficiency"):
                suggestion = "Keep the workflow/process framing, but make the CTA more specific and measurable."
            elif features.get("emphasizes_growth_outcomes"):
                suggestion = "Keep the growth and client-outcome angle, then add a sharper proof point or example."
            else:
                suggestion = "Clarify the value proposition and make the next action more concrete."
            lines.append(f"- **{persona}:** {suggestion}")
        return "\n".join(lines) if lines else "- No performance records were available for persona-specific revisions."

    def _load_json(self, file_path: Path, fallback: object) -> object:
        """Load a JSON file with a safe fallback for missing or invalid files."""
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return fallback

    def _load_text(self, file_path: Path) -> str:
        """Load a text file with a safe fallback."""
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
