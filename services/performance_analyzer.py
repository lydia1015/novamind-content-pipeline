"""Create a concise content and growth summary from simulated campaign results."""

from __future__ import annotations

from datetime import datetime

from config import LATEST_SUMMARY_FILE


class PerformanceAnalyzer:
    """Generate a plain-language campaign summary and next-step recommendations."""

    def analyze(self, topic: str, content: dict, metrics: list) -> str:
        """Build and save a markdown summary for the latest run."""
        if not metrics:
            raise ValueError("Metrics are required to generate a performance summary.")

        top_open = max(metrics, key=lambda item: self._metric_value(item, "open"))
        top_click = max(metrics, key=lambda item: self._metric_value(item, "click"))
        highest_unsubscribe = max(metrics, key=lambda item: self._metric_value(item, "unsubscribe"))

        driver_lines = self._build_driver_lines(metrics)
        recommendations = self._build_recommendations(top_open, top_click, highest_unsubscribe)

        summary = (
            f"# NovaMind Campaign Summary\n\n"
            f"**Run date:** {datetime.utcnow().isoformat()}Z\n"
            f"**Topic:** {topic}\n"
            f"**Blog title:** {content.get('blog_title')}\n\n"
            f"_Assumption: performance figures below are simulated locally using a realistic rule-based model._\n\n"
            f"## Segment Performance Snapshot\n\n"
            f"- Highest open rate: **{top_open['persona']}** at **{self._metric_value(top_open, 'open'):.1%}**\n"
            f"- Highest click rate: **{top_click['persona']}** at **{self._metric_value(top_click, 'click'):.1%}**\n"
            f"- Highest unsubscribe risk: **{highest_unsubscribe['persona']}** at **{self._metric_value(highest_unsubscribe, 'unsubscribe'):.1%}**\n\n"
            f"## Likely Content Drivers\n\n"
            f"{driver_lines}\n\n"
            f"## Recommendations For The Next Campaign\n\n"
            f"{recommendations}\n"
        )

        with LATEST_SUMMARY_FILE.open("w", encoding="utf-8") as file:
            file.write(summary)

        return summary

    def _build_driver_lines(self, metrics: list) -> str:
        """Generate a short explanation of why different segments likely performed differently."""
        lines = []
        top_open_persona = max(metrics, key=lambda item: self._metric_value(item, "open"))["persona"]
        top_click_persona = max(metrics, key=lambda item: self._metric_value(item, "click"))["persona"]
        highest_unsub_persona = max(metrics, key=lambda item: self._metric_value(item, "unsubscribe"))["persona"]

        for metric in metrics:
            features = metric.get("content_features", {})
            reason_text = self._describe_segment_driver(
                metric,
                top_open_persona=top_open_persona,
                top_click_persona=top_click_persona,
                highest_unsub_persona=highest_unsub_persona,
            )
            lines.append(
                f"- **{metric['persona']}** likely performed this way because of {reason_text}. "
                f"It finished with **{self._metric_value(metric, 'open'):.1%}** opens, "
                f"**{self._metric_value(metric, 'click'):.1%}** clicks, and "
                f"**{self._metric_value(metric, 'unsubscribe'):.1%}** unsubscribes."
            )
        return "\n".join(lines)

    def _build_recommendations(self, top_open: dict, top_click: dict, highest_unsubscribe: dict) -> str:
        """Return a concise set of practical next-step recommendations."""
        top_open_features = top_open.get("content_features", {})
        top_click_features = top_click.get("content_features", {})
        highest_unsub_features = highest_unsubscribe.get("content_features", {})

        open_pattern = self._summarize_feature_pattern(top_open_features, focus="open")
        click_pattern = self._summarize_feature_pattern(top_click_features, focus="click")
        risk_pattern = self._summarize_risk_pattern(highest_unsub_features)

        recommendations = [
            (
                f"- Reuse the strongest top-of-funnel pattern from **{top_open['persona']}** by testing more messages built around {open_pattern}."
            ),
            (
                f"- Build the next click-through test around **{top_click['persona']}**, which responded best to {click_pattern}."
            ),
            (
                f"- Tighten message-to-audience fit for **{highest_unsubscribe['persona']}**, where unsubscribe risk was highest and the current pattern suggests {risk_pattern}."
            ),
        ]

        if top_click_features.get("has_cta") and top_click_features.get("emphasizes_workflow_efficiency"):
            recommendations.append(
                f"- Test whether the CTA-plus-workflow pattern from **{top_click['persona']}** can lift engagement in other segments without increasing unsubscribe risk."
            )
        elif top_open["persona"] != top_click["persona"]:
            recommendations.append(
                "- Run a simple A/B test that combines the best-performing open driver with the best-performing click driver to see whether one version can improve both metrics together."
            )
        else:
            recommendations.append(
                f"- Keep prioritizing **{top_click['persona']}** in the next send, then test a second variant with more explicit proof points or examples to push click performance further."
            )

        return "\n".join(recommendations)

    def _describe_segment_driver(
        self,
        metric: dict,
        *,
        top_open_persona: str,
        top_click_persona: str,
        highest_unsub_persona: str,
    ) -> str:
        """Describe the main drivers for one segment without repeating the same phrasing."""
        features = metric.get("content_features", {})
        persona = metric["persona"]
        phrases = []

        if persona == top_open_persona and features.get("benefit_led_subject"):
            phrases.append("a stronger subject-line hook at the top of the funnel")
        if persona == top_click_persona and features.get("has_cta"):
            phrases.append("clear CTA language that translated attention into action")
        if features.get("persona_fit") == "high":
            phrases.append("a message angle that matched this audience especially well")
        if features.get("emphasizes_workflow_efficiency"):
            phrases.append("workflow-focused framing")
        if features.get("emphasizes_growth_outcomes"):
            phrases.append("growth and client-outcome framing")
        if features.get("preview_clear"):
            phrases.append("clear preview text that reinforced the email promise")
        if persona == highest_unsub_persona and features.get("content_length") == "long":
            phrases.append("longer copy that may have added friction")

        if not phrases and features.get("benefit_led_subject"):
            phrases.append("benefit-led framing")
        if not phrases and features.get("has_cta"):
            phrases.append("more explicit action-oriented copy")
        if not phrases:
            phrases.append("baseline audience behavior with minor natural variation")

        return ", ".join(phrases[:3])

    def _summarize_feature_pattern(self, features: dict, focus: str) -> str:
        """Turn the winning feature mix into a short recommendation phrase."""
        parts = []
        if features.get("benefit_led_subject") and focus == "open":
            parts.append("benefit-led subject lines")
        if features.get("preview_clear") and focus == "open":
            parts.append("clear preview text")
        if features.get("has_cta") and focus == "click":
            parts.append("clear CTA language")
        if features.get("emphasizes_workflow_efficiency"):
            parts.append("workflow-oriented positioning")
        if features.get("emphasizes_growth_outcomes"):
            parts.append("growth-outcome messaging")
        if features.get("persona_fit") == "high":
            parts.append("tight persona-message fit")
        return " and ".join(parts[:2]) or "the strongest-performing message structure"

    def _summarize_risk_pattern(self, features: dict) -> str:
        """Summarize the likely pattern behind higher unsubscribe risk."""
        if features.get("content_length") == "long":
            return "the audience may need a shorter, tighter version"
        if features.get("persona_fit") != "high":
            return "the value proposition may need to be narrowed for that audience"
        if not features.get("preview_clear"):
            return "the message setup may need more clarity before the open"
        return "the segment may need a more audience-specific angle"

    def _metric_value(self, metric: dict, metric_name: str) -> float:
        """Prefer modeled rates when available, falling back to stored final rates."""
        modeled_key = f"modeled_{metric_name}_rate"
        fallback_key = f"{metric_name}_rate"
        return float(metric.get(modeled_key, metric.get(fallback_key, 0.0)))
