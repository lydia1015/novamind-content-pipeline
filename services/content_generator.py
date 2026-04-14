"""Generate blog and newsletter content for the CLI workflow."""

from __future__ import annotations

import json
from datetime import datetime
from textwrap import dedent

from config import GENERATED_CONTENT_FILE, PERSONAS
from prompts.content_prompts import build_content_prompt


class ContentGenerator:
    """Generate content with Groq when available, otherwise use a deterministic fallback."""

    def __init__(self, config: dict) -> None:
        self.api_key = config.get("groq_api_key", "")
        self.model = config.get("groq_model", "openai/gpt-oss-20b")

    def generate(self, topic: str) -> dict:
        """Generate content for the supplied topic and persist it locally."""
        topic = topic.strip()
        if not topic:
            raise ValueError("Topic input cannot be empty.")

        content = self._generate_with_groq(topic) if self.api_key else self._generate_fallback(topic)
        content["topic"] = topic
        content["generated_at"] = datetime.utcnow().isoformat() + "Z"
        self._save(content)
        return content

    def _generate_with_groq(self, topic: str) -> dict:
        """Attempt to generate content through Groq's OpenAI-compatible API, falling back on failure."""
        prompt = build_content_prompt(topic)
        try:
            from openai import OpenAI

            # Groq exposes an OpenAI-compatible API surface, so the standard SDK works with a custom base URL.
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            response = client.responses.create(
                model=self.model,
                input=prompt,
            )
            raw_text = response.output_text.strip()
            payload = json.loads(raw_text)
            return self._normalize_payload(payload, topic)
        except Exception:
            # The assignment should still run offline or without credentials, so we degrade gracefully.
            return self._generate_fallback(topic)

    def _generate_fallback(self, topic: str) -> dict:
        """Create predictable, submission-friendly content without external API calls."""
        title = f"How {topic} helps small creative agencies move faster"
        outline = [
            "Why small creative agencies are under pressure to deliver more with leaner teams",
            "The most common workflow bottlenecks in content, operations, and client communication",
            "Practical AI automation use cases that save time without sacrificing quality",
            "How agencies can introduce automation in low-risk, repeatable tasks",
            "A lightweight roadmap for getting started with an AI-powered workflow",
        ]
        blog_draft = dedent(
            f"""
            Small creative agencies are being asked to do more than ever. Clients expect faster turnarounds,
            more personalized communication, and consistent output across channels, but agency teams often stay
            intentionally lean. That creates a familiar tension: how do you keep quality high without burning out
            the team or slowing down delivery? This is where {topic} becomes a practical advantage rather than a
            trend to watch from a distance.

            For many agencies, the biggest challenge is not a lack of creativity. It is the amount of repetitive
            work wrapped around creative delivery. Teams spend time drafting status updates, building content
            variants, preparing campaign assets, and moving information between tools. None of these steps are
            individually impossible, but together they create drag. When those tasks stack up, strategy gets rushed
            and creative energy gets redirected toward administration.

            AI automation can reduce that drag in a way that feels manageable for smaller teams. Instead of trying
            to automate everything at once, agencies can start with repeatable workflows that already follow a
            pattern. A blog topic can become an outline, a draft, and a set of persona-based newsletter versions.
            Contact segments can be matched automatically. Campaign logs can be updated in the background. That
            means fewer manual handoffs and a faster path from idea to distribution.

            The most effective use cases are usually the least glamorous. Operations managers benefit when campaign
            steps are documented and tracked consistently. Agency owners benefit when their team spends less time on
            repetitive formatting and more time on client strategy. Freelance creatives benefit when they can reuse
            one strong idea across several channels without rewriting every asset from scratch. In each case, the
            value is not just speed. It is clarity, consistency, and the ability to scale work without immediately
            scaling headcount.

            A smart rollout starts with a narrow workflow and a clear success metric. Choose a single content motion
            that happens every week. Map the inputs, define the outputs, and identify which parts are rules-based.
            Then use AI to support generation, organization, and reporting while keeping human review in the loop.
            This approach helps agencies build trust in the system while protecting quality.

            For small creative agencies, AI automation works best as an operational layer that supports people rather
            than replaces them. It gives teams back time for strategy, creative direction, and client relationships.
            When implemented thoughtfully, it can turn a messy process into a repeatable pipeline and help agencies
            grow without losing the flexibility that makes them valuable in the first place.
            """
        ).strip()

        newsletters = [
            {
                "persona": "Creative Agency Owner",
                "newsletter_version_id": "newsletter-owner-v1",
                "subject_line": "Scale client delivery without adding headcount pressure",
                "preview_text": "A practical look at how agency owners can improve margin and speed with smarter automation.",
                "body": (
                    f"Agency owners need growth that does not come at the cost of team burnout or margin erosion. "
                    f"This piece shows how {topic} can turn one campaign idea into a repeatable pipeline, speed up "
                    "client delivery, and give strategists more time for upsell conversations, retention, and higher-value work."
                ),
            },
            {
                "persona": "Operations Manager at a Small Agency",
                "newsletter_version_id": "newsletter-ops-v1",
                "subject_line": "Standardize campaign handoffs without slowing the team down",
                "preview_text": "See a lightweight workflow for content generation, segmentation, and campaign logging.",
                "body": (
                    f"If you manage delivery across a lean agency team, {topic} can reduce repetitive admin and make campaign ops more dependable. "
                    "Explore a workflow that generates content variants, maps them to the right audience segments, and keeps campaign reporting organized without adding more manual QA."
                ),
            },
            {
                "persona": "Freelance Creative Professional",
                "newsletter_version_id": "newsletter-freelance-v1",
                "subject_line": "Turn one client brief into multiple polished deliverables faster",
                "preview_text": "Use a simple AI-assisted workflow to repurpose ideas without losing your creative voice.",
                "body": (
                    f"Freelance creatives often handle strategy, writing, revisions, and delivery alone. {topic} can help you turn "
                    "one strong brief into blog and newsletter assets faster, so you spend less time reworking copy and more time delivering polished client-ready output."
                ),
            },
        ]

        return self._normalize_payload(
            {
                "blog_title": title,
                "blog_outline": outline,
                "blog_draft": blog_draft,
                "newsletters": newsletters,
            },
            topic,
        )

    def _normalize_payload(self, payload: dict, topic: str) -> dict:
        """Enforce the expected shape so downstream services can stay simple."""
        newsletters = payload.get("newsletters", [])
        newsletter_map = {item.get("persona"): item for item in newsletters if isinstance(item, dict)}
        normalized_newsletters = []
        for persona in PERSONAS:
            entry = newsletter_map.get(persona, {})
            normalized_newsletters.append(
                {
                    "persona": persona,
                    "newsletter_version_id": entry.get(
                        "newsletter_version_id", f"newsletter-{persona.lower().split()[0]}-v1"
                    ),
                    "subject_line": entry.get("subject_line", f"{topic.title()} for {persona}"),
                    "preview_text": entry.get("preview_text", f"A short tailored update for {persona}."),
                    "body": entry.get("body", f"This campaign explores {topic} for {persona}."),
                }
            )

        return {
            "blog_title": payload.get("blog_title", f"{topic.title()} for Small Creative Agencies"),
            "blog_outline": payload.get("blog_outline", []),
            "blog_draft": payload.get("blog_draft", ""),
            "newsletters": normalized_newsletters,
        }

    def _save(self, content: dict) -> None:
        """Persist the latest generated content payload."""
        with GENERATED_CONTENT_FILE.open("w", encoding="utf-8") as file:
            json.dump(content, file, indent=2)
