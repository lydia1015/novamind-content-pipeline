"""Simulate newsletter performance with simple rule-based logic."""

from __future__ import annotations

import hashlib

from config import PERFORMANCE_HISTORY_FILE
from services.campaign_logger import CampaignLogger


class MetricsSimulator:
    """Generate realistic, explainable performance records for each persona segment."""

    PERSONA_BASELINES = {
        "Creative Agency Owner": {
            "open_rate": 0.41,
            "click_rate": 0.12,
            "unsubscribe_rate": 0.018,
        },
        "Operations Manager at a Small Agency": {
            "open_rate": 0.46,
            "click_rate": 0.15,
            "unsubscribe_rate": 0.014,
        },
        "Freelance Creative Professional": {
            "open_rate": 0.39,
            "click_rate": 0.11,
            "unsubscribe_rate": 0.02,
        },
    }

    CTA_TERMS = ("see how", "explore", "learn", "discover", "start", "book", "download", "try")
    CASE_STUDY_TERMS = ("case study", "for example", "example", "real-world", "client story", "proof")
    WORKFLOW_TERMS = ("workflow", "process", "handoff", "campaign ops", "efficiency", "standardize")
    GROWTH_TERMS = ("growth", "margin", "retention", "client", "upsell", "revenue", "capacity")

    def __init__(self) -> None:
        self.logger = CampaignLogger()

    def simulate(self, topic: str, campaign_entries: list) -> list:
        """Simulate metrics for each persona segment and persist richer performance history records."""
        metrics = []
        for entry in campaign_entries:
            recipient_count = int(entry.get("total_contacts", 0))
            if recipient_count <= 0:
                result = self._empty_result(entry)
                self.logger.append_record(PERFORMANCE_HISTORY_FILE, result)
                metrics.append(result)
                continue

            subject_line = entry.get("subject_line", "")
            preview_text = entry.get("preview_text", "")
            newsletter_body = entry.get("newsletter_body", "")

            content_features = self._extract_content_features(
                entry["persona"], subject_line, preview_text, newsletter_body
            )
            reasoning_notes = self._build_reasoning_notes(content_features)

            delivered_count = self._simulate_delivered_count(topic, entry, recipient_count)
            modeled_open_rate = self._simulate_open_rate(topic, entry, content_features, delivered_count)
            modeled_click_rate = self._simulate_click_rate(
                topic, entry, content_features, delivered_count, modeled_open_rate
            )
            modeled_unsubscribe_rate = self._simulate_unsubscribe_rate(
                topic, entry, content_features, delivered_count
            )

            opened_count = min(delivered_count, round(delivered_count * modeled_open_rate))
            clicked_count = min(opened_count, round(delivered_count * modeled_click_rate))
            unsubscribed_count = min(delivered_count - clicked_count, round(delivered_count * modeled_unsubscribe_rate))

            result = {
                "campaign_id": entry["campaign_id"],
                "run_timestamp": entry.get("send_date"),
                "blog_title": entry["blog_title"],
                "persona": entry["persona"],
                "newsletter_version_id": entry["newsletter_version_id"],
                "simulation_mode": "realistic_rule_based",
                "recipient_count": recipient_count,
                "delivered_count": delivered_count,
                "opened_count": opened_count,
                "clicked_count": clicked_count,
                "unsubscribed_count": unsubscribed_count,
                "subject_line": subject_line,
                "preview_text": preview_text,
                "content_features": content_features,
                "reasoning_notes": reasoning_notes,
                "modeled_open_rate": round(modeled_open_rate, 3),
                "modeled_click_rate": round(modeled_click_rate, 3),
                "modeled_unsubscribe_rate": round(modeled_unsubscribe_rate, 3),
                # For small demo audiences, modeled rates are more analytically useful than realized count ratios.
                "open_rate": round(modeled_open_rate, 3),
                "click_rate": round(modeled_click_rate, 3),
                "unsubscribe_rate": round(modeled_unsubscribe_rate, 3),
                "total_contacts": recipient_count,
            }
            self.logger.append_record(PERFORMANCE_HISTORY_FILE, result)
            metrics.append(result)
        return metrics

    def _empty_result(self, entry: dict) -> dict:
        """Return a safe empty record for segments with no recipients."""
        return {
            "campaign_id": entry["campaign_id"],
            "run_timestamp": entry.get("send_date"),
            "blog_title": entry["blog_title"],
            "persona": entry["persona"],
            "newsletter_version_id": entry["newsletter_version_id"],
            "simulation_mode": "realistic_rule_based",
            "recipient_count": 0,
            "delivered_count": 0,
            "opened_count": 0,
            "clicked_count": 0,
            "unsubscribed_count": 0,
            "subject_line": entry.get("subject_line", ""),
            "preview_text": entry.get("preview_text", ""),
            "content_features": {},
            "reasoning_notes": ["No recipients were available in this segment."],
            "modeled_open_rate": 0.0,
            "modeled_click_rate": 0.0,
            "modeled_unsubscribe_rate": 0.0,
            "open_rate": 0.0,
            "click_rate": 0.0,
            "unsubscribe_rate": 0.0,
            "total_contacts": 0,
        }

    def _extract_content_features(self, persona: str, subject_line: str, preview_text: str, body: str) -> dict:
        """Extract a few lightweight features that influence simulated performance."""
        combined = " ".join([subject_line, preview_text, body]).lower()
        body_word_count = len(body.split())

        preview_clear = 0 < len(preview_text.split()) <= 18
        has_cta = any(term in combined for term in self.CTA_TERMS)
        has_case_study_language = any(term in combined for term in self.CASE_STUDY_TERMS)
        emphasizes_workflow = any(term in combined for term in self.WORKFLOW_TERMS)
        emphasizes_growth = any(term in combined for term in self.GROWTH_TERMS)
        benefit_led_subject = any(word in subject_line.lower() for word in ("scale", "standardize", "turn", "grow"))

        if body_word_count < 25:
            content_length = "short"
        elif body_word_count <= 55:
            content_length = "balanced"
        else:
            content_length = "long"

        persona_fit = "medium"
        if persona == "Operations Manager at a Small Agency" and emphasizes_workflow:
            persona_fit = "high"
        elif persona == "Creative Agency Owner" and emphasizes_growth:
            persona_fit = "high"
        elif persona == "Freelance Creative Professional" and ("deliverable" in combined or "brief" in combined):
            persona_fit = "high"

        return {
            "preview_clear": preview_clear,
            "has_cta": has_cta,
            "has_case_study_language": has_case_study_language,
            "emphasizes_workflow_efficiency": emphasizes_workflow,
            "emphasizes_growth_outcomes": emphasizes_growth,
            "content_length": content_length,
            "benefit_led_subject": benefit_led_subject,
            "persona_fit": persona_fit,
        }

    def _build_reasoning_notes(self, features: dict) -> list:
        """Generate concise notes explaining the main simulated drivers."""
        notes = []
        if features.get("persona_fit") == "high":
            notes.append("The message angle aligned well with this persona's priorities.")
        if features.get("benefit_led_subject"):
            notes.append("A benefit-led subject line supported stronger open performance.")
        if features.get("preview_clear"):
            notes.append("A concise preview text improved message clarity.")
        if features.get("has_cta"):
            notes.append("Clear CTA language supported click intent.")
        if features.get("has_case_study_language"):
            notes.append("Example-driven language added credibility.")
        if features.get("emphasizes_workflow_efficiency"):
            notes.append("Workflow-focused language increased relevance for process-oriented readers.")
        if features.get("emphasizes_growth_outcomes"):
            notes.append("Growth-oriented messaging strengthened commercial relevance.")
        if features.get("content_length") == "long":
            notes.append("Longer copy slightly reduced downstream engagement.")
        return notes or ["Performance was driven mostly by baseline persona behavior and minor natural variation."]

    def _simulate_delivered_count(self, topic: str, entry: dict, recipient_count: int) -> int:
        """Simulate a realistic delivered count with a very small bounce adjustment."""
        noise = self._stable_noise(topic, entry["persona"], "deliverability")
        bounce_rate = self._clamp(0.01 + abs(noise) * 0.02, 0.005, 0.03)
        return max(0, round(recipient_count * (1 - bounce_rate)))

    def _simulate_open_rate(self, topic: str, entry: dict, features: dict, delivered_count: int) -> float:
        """Simulate open rate from persona baseline plus a few explainable adjustments."""
        baseline = self.PERSONA_BASELINES[entry["persona"]]["open_rate"]
        rate = baseline

        if features.get("benefit_led_subject"):
            rate += 0.02
        if features.get("preview_clear"):
            rate += 0.01
        if features.get("persona_fit") == "high":
            rate += 0.015
        if delivered_count < 10:
            rate -= 0.005
        elif delivered_count > 50:
            rate += 0.005

        rate += self._stable_noise(topic, entry["persona"], "open")
        return self._clamp(rate, 0.18, 0.68)

    def _simulate_click_rate(
        self,
        topic: str,
        entry: dict,
        features: dict,
        delivered_count: int,
        modeled_open_rate: float,
    ) -> float:
        """Simulate click rate using CTA, specificity, message angle, and top-of-funnel attention."""
        baseline = self.PERSONA_BASELINES[entry["persona"]]["click_rate"]
        rate = baseline

        if features.get("has_cta"):
            rate += 0.02
        if features.get("has_case_study_language"):
            rate += 0.01
        if features.get("emphasizes_workflow_efficiency") and entry["persona"] == "Operations Manager at a Small Agency":
            rate += 0.015
        if features.get("emphasizes_growth_outcomes") and entry["persona"] == "Creative Agency Owner":
            rate += 0.015
        if features.get("content_length") == "long":
            rate -= 0.01
        if modeled_open_rate < 0.3:
            rate -= 0.005

        rate += self._stable_noise(topic, entry["persona"], "click")
        return self._clamp(rate, 0.03, 0.28)

    def _simulate_unsubscribe_rate(self, topic: str, entry: dict, features: dict, delivered_count: int) -> float:
        """Simulate unsubscribe rate with small penalties for weaker fit or longer copy."""
        baseline = self.PERSONA_BASELINES[entry["persona"]]["unsubscribe_rate"]
        rate = baseline

        if features.get("persona_fit") != "high":
            rate += 0.003
        if features.get("content_length") == "long":
            rate += 0.003
        if features.get("preview_clear"):
            rate -= 0.002
        if delivered_count < 10:
            rate += 0.002

        rate += abs(self._stable_noise(topic, entry["persona"], "unsubscribe")) / 2
        return self._clamp(rate, 0.005, 0.06)

    def _stable_noise(self, topic: str, persona: str, label: str) -> float:
        """Add small bounded variation so repeated runs feel natural but still deterministic."""
        digest = hashlib.sha256(f"{topic.lower()}::{persona}::{label}".encode("utf-8")).hexdigest()
        scaled = int(digest[:4], 16) / 65535
        return round((scaled - 0.5) * 0.02, 4)

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        """Clamp a simulated value into a realistic range."""
        return min(max(value, minimum), maximum)
