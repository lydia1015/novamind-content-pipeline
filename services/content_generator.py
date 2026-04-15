"""Generate blog and newsletter content for the CLI workflow."""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from datetime import datetime
from textwrap import dedent

from config import GENERATED_CONTENT_FILE, PERSONAS


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
        try:
            from openai import OpenAI

            # Groq exposes an OpenAI-compatible API surface, so the standard SDK works with a custom base URL.
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            blog_payload = self._call_groq_json(
                client=client,
                prompt=self._build_blog_prompt(topic),
                schema_name="novamind_blog_content",
                schema=self._blog_schema(),
            )
            newsletter_payload = self._call_groq_json(
                client=client,
                prompt=self._build_newsletter_prompt(topic, blog_payload["blog_title"]),
                schema_name="novamind_newsletter_content",
                schema=self._newsletter_schema(),
            )
            payload = {**blog_payload, **newsletter_payload}
            try:
                variant_payload = self._call_groq_json(
                    client=client,
                    prompt=self._build_variant_prompt(topic, payload),
                    schema_name="novamind_copy_variants",
                    schema=self._variant_schema(),
                )
                payload = self._merge_variants(payload, variant_payload)
            except Exception as variant_exc:
                print(f"Groq variant generation failed: {variant_exc}")
            print("Content generation mode: Groq")
            return self._normalize_payload(payload, topic)
        except Exception as exc:
            # The assignment should still run offline or without credentials, so we degrade gracefully.
            print(f"Groq generation failed: {exc}")
            return self._generate_fallback(topic)

    def _generate_fallback(self, topic: str) -> dict:
        """Create predictable, submission-friendly content without external API calls."""
        print("Content generation mode: Local fallback")
        title_options = [
            f"How {topic} helps small creative agencies move faster",
            f"A practical guide to {topic} for lean creative teams",
            f"Why small agencies are turning to {topic} to scale smarter",
        ]
        outline_options = [
            {
                "outline_id": "outline-speed-and-scale",
                "items": [
                    "Why small creative agencies are under pressure to deliver more with leaner teams",
                    "The most common workflow bottlenecks in content, operations, and client communication",
                    "Practical AI automation use cases that save time without sacrificing quality",
                    "How agencies can introduce automation in low-risk, repeatable tasks",
                    "A lightweight roadmap for getting started with an AI-powered workflow",
                ],
            },
            {
                "outline_id": "outline-growth-operations",
                "items": [
                    "How operational drag limits agency growth and client responsiveness",
                    "Where AI can help turn one idea into multiple campaign assets",
                    "How persona-based content improves relevance across audience segments",
                    "Why CRM logging and performance summaries matter for growth teams",
                    "Next steps for testing a repeatable AI-assisted campaign workflow",
                ],
            },
        ]
        selected_title = title_options[0]
        selected_outline = outline_options[0]
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
                "subject_line_options": [
                    "Scale client delivery without adding headcount pressure",
                    "Protect agency margin with a smarter AI-assisted content workflow",
                ],
                "preview_text_options": [
                    "A practical look at how agency owners can improve margin and speed with smarter automation.",
                    "Turn one campaign idea into more output without stretching the team.",
                ],
                "body_options": [
                    {
                        "angle": "growth-and-margin",
                        "body": (
                            f"Agency owners need growth that does not come at the cost of team burnout or margin erosion. "
                            f"This piece shows how {topic} can turn one campaign idea into a repeatable pipeline, speed up "
                            "client delivery, and give strategists more time for upsell conversations, retention, and higher-value work."
                        ),
                    },
                    {
                        "angle": "capacity-planning",
                        "body": (
                            f"When client requests increase, agency owners need more leverage without immediately adding headcount. "
                            f"This campaign shows how {topic} can improve content throughput, reduce manual coordination, and make growth feel more manageable."
                        ),
                    },
                ],
                "selected_subject_line": "Scale client delivery without adding headcount pressure",
                "selected_preview_text": "A practical look at how agency owners can improve margin and speed with smarter automation.",
                "selected_body_angle": "growth-and-margin",
                "selected_body": (
                    f"Agency owners need growth that does not come at the cost of team burnout or margin erosion. "
                    f"This piece shows how {topic} can turn one campaign idea into a repeatable pipeline, speed up "
                    "client delivery, and give strategists more time for upsell conversations, retention, and higher-value work."
                ),
            },
            {
                "persona": "Operations Manager at a Small Agency",
                "newsletter_version_id": "newsletter-ops-v1",
                "subject_line_options": [
                    "Standardize campaign handoffs without slowing the team down",
                    "A lighter way to manage agency campaign ops",
                ],
                "preview_text_options": [
                    "See a lightweight workflow for content generation, segmentation, and campaign logging.",
                    "Reduce repetitive admin while keeping every campaign step easier to track.",
                ],
                "body_options": [
                    {
                        "angle": "workflow-efficiency",
                        "body": (
                            f"If you manage delivery across a lean agency team, {topic} can reduce repetitive admin and make campaign ops more dependable. "
                            "Explore a workflow that generates content variants, maps them to the right audience segments, and keeps campaign reporting organized without adding more manual QA."
                        ),
                    },
                    {
                        "angle": "handoff-clarity",
                        "body": (
                            f"Agency operations teams need repeatable systems that keep creative work moving. "
                            f"This workflow uses {topic} to simplify handoffs, document campaign steps, and make reporting cleaner after every send."
                        ),
                    },
                ],
                "selected_subject_line": "Standardize campaign handoffs without slowing the team down",
                "selected_preview_text": "See a lightweight workflow for content generation, segmentation, and campaign logging.",
                "selected_body_angle": "workflow-efficiency",
                "selected_body": (
                    f"If you manage delivery across a lean agency team, {topic} can reduce repetitive admin and make campaign ops more dependable. "
                    "Explore a workflow that generates content variants, maps them to the right audience segments, and keeps campaign reporting organized without adding more manual QA."
                ),
            },
            {
                "persona": "Freelance Creative Professional",
                "newsletter_version_id": "newsletter-freelance-v1",
                "subject_line_options": [
                    "Turn one client brief into multiple polished deliverables faster",
                    "Repurpose client ideas without losing your creative voice",
                ],
                "preview_text_options": [
                    "Use a simple AI-assisted workflow to repurpose ideas without losing your creative voice.",
                    "Move from brief to blog and newsletter assets with less rewriting.",
                ],
                "body_options": [
                    {
                        "angle": "solo-creator-productivity",
                        "body": (
                            f"Freelance creatives often handle strategy, writing, revisions, and delivery alone. {topic} can help you turn "
                            "one strong brief into blog and newsletter assets faster, so you spend less time reworking copy and more time delivering polished client-ready output."
                        ),
                    },
                    {
                        "angle": "client-delivery-speed",
                        "body": (
                            f"When you are running the whole client workflow yourself, every repeatable step matters. "
                            f"This piece shows how {topic} can help freelancers draft faster, adapt ideas across channels, and keep deadlines under control."
                        ),
                    },
                ],
                "selected_subject_line": "Turn one client brief into multiple polished deliverables faster",
                "selected_preview_text": "Use a simple AI-assisted workflow to repurpose ideas without losing your creative voice.",
                "selected_body_angle": "solo-creator-productivity",
                "selected_body": (
                    f"Freelance creatives often handle strategy, writing, revisions, and delivery alone. {topic} can help you turn "
                    "one strong brief into blog and newsletter assets faster, so you spend less time reworking copy and more time delivering polished client-ready output."
                ),
            },
        ]

        return self._normalize_payload(
            {
                "blog_title_options": title_options,
                "selected_blog_title": selected_title,
                "outline_options": outline_options,
                "selected_outline_id": selected_outline["outline_id"],
                "blog_draft": blog_draft,
                "newsletters": newsletters,
            },
            topic,
        )

    def _normalize_payload(self, payload: dict, topic: str) -> dict:
        """Enforce the expected shape so downstream services can stay simple."""
        title_options = self._ensure_list(
            payload.get("blog_title_options") or payload.get("title_options"),
            [payload.get("blog_title", f"{topic.title()} for Small Creative Agencies")],
        )
        title_options = self._pad_options(
            title_options,
            self._support_title_options(topic),
            3,
            minimum=2,
        )
        selected_blog_title = payload.get("selected_blog_title") or payload.get("blog_title") or title_options[0]
        if selected_blog_title not in title_options:
            title_options[0] = selected_blog_title

        outline_options = self._normalize_outline_options(payload, topic)
        selected_outline_id = payload.get("selected_outline_id") or outline_options[0]["outline_id"]
        selected_outline = next(
            (outline for outline in outline_options if outline["outline_id"] == selected_outline_id),
            outline_options[0],
        )

        newsletters = payload.get("newsletters", [])
        newsletter_map = {item.get("persona"): item for item in newsletters if isinstance(item, dict)}
        normalized_newsletters = []
        for persona in PERSONAS:
            entry = newsletter_map.get(persona, {})
            subject_options = self._pad_options(
                self._ensure_list(entry.get("subject_line_options"), [entry.get("subject_line")]),
                self._support_subject_options(topic, persona),
                3,
                minimum=2,
            )
            preview_options = self._pad_options(
                self._ensure_list(entry.get("preview_text_options"), [entry.get("preview_text")]),
                self._support_preview_options(topic, persona),
                3,
                minimum=2,
            )
            body_options = self._normalize_body_options(entry, topic, persona)
            selected_body_angle = entry.get("selected_body_angle") or body_options[0]["angle"]
            selected_body = entry.get("selected_body") or entry.get("body") or body_options[0]["body"]
            if selected_body_angle not in {option["angle"] for option in body_options}:
                selected_body_angle = body_options[0]["angle"]
            if selected_body not in {option["body"] for option in body_options}:
                body_options[0]["body"] = selected_body

            selected_subject = entry.get("selected_subject_line") or entry.get("subject_line") or subject_options[0]
            selected_preview = entry.get("selected_preview_text") or entry.get("preview_text") or preview_options[0]
            if selected_subject not in subject_options:
                subject_options[0] = selected_subject
            if selected_preview not in preview_options:
                preview_options[0] = selected_preview

            normalized_newsletters.append(
                {
                    "persona": persona,
                    "newsletter_version_id": entry.get(
                        "newsletter_version_id", f"newsletter-{persona.lower().split()[0]}-v1"
                    ),
                    "subject_line_options": subject_options,
                    "selected_subject_line": selected_subject,
                    "subject_line": selected_subject,
                    "preview_text_options": preview_options,
                    "selected_preview_text": selected_preview,
                    "preview_text": selected_preview,
                    "body_options": body_options,
                    "selected_body_angle": selected_body_angle,
                    "selected_body": selected_body,
                    "body": selected_body,
                }
            )

        return {
            "blog_title_options": title_options,
            "selected_blog_title": selected_blog_title,
            "blog_title": selected_blog_title,
            "outline_options": outline_options,
            "selected_outline_id": selected_outline["outline_id"],
            "blog_outline": selected_outline["items"],
            "blog_draft": payload.get("blog_draft", ""),
            "newsletters": normalized_newsletters,
        }

    def _normalize_outline_options(self, payload: dict, topic: str) -> list:
        """Normalize outline candidates while preserving a final selected outline for downstream use."""
        fallback_outline = payload.get("blog_outline") or [
            f"Why {topic} matters for small creative agencies",
            "Where repetitive workflow tasks slow teams down",
            "How AI-assisted content and CRM workflows can help",
            "What to test in the first campaign",
        ]
        raw_options = payload.get("outline_options")
        if not isinstance(raw_options, list) or not raw_options:
            raw_options = [{"outline_id": "outline-primary", "items": fallback_outline}]

        normalized = []
        for index, option in enumerate(raw_options[:2], start=1):
            if isinstance(option, dict):
                items = self._ensure_list(option.get("items"), fallback_outline)
                outline_id = option.get("outline_id", f"outline-{index}")
            else:
                items = self._ensure_list(option, fallback_outline)
                outline_id = f"outline-{index}"
            outline_text = " ".join(str(item) for item in items)
            existing_texts = [" ".join(str(item) for item in outline["items"]) for outline in normalized]
            if items and not any(self._is_similar_text(outline_text, existing_text) for existing_text in existing_texts):
                normalized.append({"outline_id": outline_id, "items": items})

        return normalized

    def _normalize_body_options(self, entry: dict, topic: str, persona: str) -> list:
        """Normalize body angle candidates for one newsletter persona."""
        fallback_body = entry.get("body") or entry.get("selected_body") or f"This campaign explores {topic} for {persona}."
        raw_options = entry.get("body_options")
        if not isinstance(raw_options, list):
            raw_options = [{"angle": "primary", "body": fallback_body}]

        normalized = []
        for index, option in enumerate(raw_options[:2], start=1):
            if isinstance(option, dict):
                normalized.append(
                    {
                        "angle": option.get("angle", f"angle-{index}"),
                        "body": option.get("body", fallback_body),
                    }
                )
            else:
                normalized.append({"angle": f"angle-{index}", "body": str(option)})

        normalized = self._dedupe_body_options(normalized, limit=2)
        if len(normalized) == 1:
            backup = self._local_body_backup(topic, persona)
            if not self._is_similar_text(normalized[0]["body"], backup):
                normalized.append({"angle": "practical-next-step", "body": backup})
        return normalized[:2]

    def _merge_variants(self, payload: dict, variant_payload: dict) -> dict:
        """Merge optional Groq copy variants into the compact core content payload."""
        merged = dict(payload)
        selected_title = payload.get("blog_title", "")
        title_variants = self._ensure_list(variant_payload.get("blog_title_variants"), [])
        merged["blog_title_options"] = self._dedupe_text_options([selected_title] + title_variants, limit=3)
        merged["selected_blog_title"] = selected_title

        variants_by_persona = {
            item.get("persona"): item
            for item in variant_payload.get("newsletter_variants", [])
            if isinstance(item, dict)
        }
        enriched_newsletters = []
        for newsletter in payload.get("newsletters", []):
            entry = dict(newsletter)
            persona = entry.get("persona")
            variant = variants_by_persona.get(persona, {})
            subject_variants = self._ensure_list(variant.get("subject_line_variants"), [])
            preview_variants = self._ensure_list(variant.get("preview_text_variants"), [])
            body_variant = variant.get("body_angle_variant", {})

            entry["subject_line_options"] = self._dedupe_text_options(
                [entry.get("subject_line", "")] + subject_variants,
                limit=3,
            )
            entry["preview_text_options"] = self._dedupe_text_options(
                [entry.get("preview_text", "")] + preview_variants,
                limit=3,
            )
            entry["body_options"] = self._dedupe_body_options(
                [
                    {"angle": "primary", "body": entry.get("body", "")},
                    {
                        "angle": body_variant.get("angle", "alternate-angle"),
                        "body": body_variant.get("body", entry.get("body", "")),
                    },
                ],
                limit=2,
            )
            entry["selected_subject_line"] = entry.get("subject_line", "")
            entry["selected_preview_text"] = entry.get("preview_text", "")
            entry["selected_body_angle"] = "primary"
            entry["selected_body"] = entry.get("body", "")
            enriched_newsletters.append(entry)

        merged["newsletters"] = enriched_newsletters
        return merged

    def _ensure_list(self, value: object, fallback: list) -> list:
        """Return a clean list of non-empty values."""
        if isinstance(value, list):
            cleaned = [item for item in value if item]
            return cleaned or [item for item in fallback if item]
        if value:
            return [value]
        return [item for item in fallback if item]

    def _pad_options(self, current: list, fallback: list, count: int, minimum: int = 1) -> list:
        """Deduplicate options and add just enough polished support variants."""
        options = self._dedupe_text_options(current, limit=count)
        for item in fallback:
            if len(options) >= min(minimum, count):
                break
            candidate = str(item).strip() if item else ""
            if candidate and not any(self._is_similar_text(candidate, existing) for existing in options):
                options.append(candidate)
        return options[:count]

    def _dedupe_text_options(self, values: list, limit: int) -> list:
        """Keep distinct text options, preserving the original order."""
        options = []
        for value in values:
            text = str(value).strip() if value else ""
            if text and not any(self._is_similar_text(text, existing) for existing in options):
                options.append(text)
            if len(options) >= limit:
                break
        return options

    def _dedupe_body_options(self, options: list, limit: int) -> list:
        """Keep distinct body options without duplicating nearly identical copy."""
        deduped = []
        for option in options:
            if not isinstance(option, dict):
                continue
            body = str(option.get("body", "")).strip()
            if body and not any(self._is_similar_text(body, existing["body"]) for existing in deduped):
                deduped.append({"angle": option.get("angle", f"angle-{len(deduped) + 1}"), "body": body})
            if len(deduped) >= limit:
                break
        return deduped

    def _is_similar_text(self, first: str, second: str) -> bool:
        """Return True when two options are close enough to feel duplicative."""
        first_clean = " ".join(first.lower().split())
        second_clean = " ".join(second.lower().split())
        if not first_clean or not second_clean:
            return False
        if first_clean == second_clean:
            return True
        return SequenceMatcher(None, first_clean, second_clean).ratio() >= 0.86

    def _local_body_backup(self, topic: str, persona: str) -> str:
        """Create one light backup angle only when Groq provided no alternate body."""
        if persona == "Creative Agency Owner":
            return (
                "Turn one repeatable client workflow into a margin-friendly delivery system that helps the team "
                "ship more consistently without adding another layer of manual coordination."
            )
        if persona == "Operations Manager at a Small Agency":
            return (
                "Give your team a cleaner path from brief to send: fewer handoff gaps, clearer campaign steps, "
                "and a simple way to see what moved before the next client deadline."
            )
        return (
            "Move from brief to polished multi-channel copy with less rewriting, so client work feels faster "
            "without flattening your creative voice."
        )

    def _support_title_options(self, topic: str) -> list:
        """Return polished backup blog titles used only when Groq variants are sparse."""
        return [
            "How lean creative teams can turn repeat work into a faster content engine",
            "A small-agency playbook for cleaner client delivery with AI support",
            f"Where {topic} creates the most leverage for creative teams",
        ]

    def _support_subject_options(self, topic: str, persona: str) -> list:
        """Return audience-facing subject backups for sparse Groq variants."""
        if persona == "Creative Agency Owner":
            return [
                "Protect margin while your team ships more client work",
                "A leaner way to scale agency delivery",
            ]
        if persona == "Operations Manager at a Small Agency":
            return [
                "Clean up campaign handoffs before the next deadline",
                "Make every campaign step easier to track",
            ]
        return [
            "Turn one brief into more usable client assets",
            "Draft faster without losing your creative voice",
        ]

    def _support_preview_options(self, topic: str, persona: str) -> list:
        """Return audience-facing preview backups for sparse Groq variants."""
        if persona == "Creative Agency Owner":
            return [
                "See how a focused AI workflow can improve delivery speed without adding headcount.",
                "Build more client capacity while keeping strategy and quality in the loop.",
            ]
        if persona == "Operations Manager at a Small Agency":
            return [
                "A practical workflow for reducing admin, clarifying handoffs, and keeping campaigns moving.",
                "Help the team move from content idea to logged campaign with fewer loose ends.",
            ]
        return [
            "Repurpose one strong idea into client-ready assets with less manual rewriting.",
            "Use AI support to move faster while keeping the work polished and personal.",
        ]

    def _save(self, content: dict) -> None:
        """Persist the latest generated content payload."""
        with GENERATED_CONTENT_FILE.open("w", encoding="utf-8") as file:
            json.dump(content, file, indent=2)

    def _call_groq_json(self, client: object, prompt: str, schema_name: str, schema: dict) -> dict:
        """Call Groq with a small JSON schema and return the parsed payload."""
        response = client.responses.create(
            model=self.model,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        return json.loads(response.output_text.strip())

    def _build_blog_prompt(self, topic: str) -> str:
        """Ask Groq for only the blog core content."""
        return (
            f"Generate blog content for this topic: {topic}\n\n"
            "Return only the fields required by the JSON schema.\n\n"
            "Requirements:\n"
            "- Write for NovaMind, an AI startup helping small creative agencies automate daily workflows.\n"
            "- Include one strong blog_title.\n"
            "- Include one blog_draft of approximately 400-600 words.\n"
            "- Keep the tone practical, clear, and useful for a content and growth analyst take-home project."
        )

    def _build_newsletter_prompt(self, topic: str, blog_title: str) -> str:
        """Ask Groq for only the newsletter core content."""
        personas = "\n".join(f"- {persona}" for persona in PERSONAS)
        return (
            f"Generate newsletter content for this blog topic: {topic}\n"
            f"Blog title: {blog_title}\n\n"
            "Return only the fields required by the JSON schema.\n\n"
            "Requirements:\n"
            "- Write for NovaMind, an AI startup helping small creative agencies automate daily workflows.\n"
            "- Include exactly three newsletters, one for each persona below.\n"
            "- Keep each newsletter concise, persona-specific, and useful for a content and growth campaign.\n"
            "- Use these exact persona names:\n"
            f"{personas}"
        )

    def _build_variant_prompt(self, topic: str, payload: dict) -> str:
        """Ask Groq for lightweight copy variants only."""
        core_content = json.dumps(
            {
                "blog_title": payload.get("blog_title", ""),
                "newsletters": payload.get("newsletters", []),
            },
            indent=2,
        )
        return (
            f"Generate lightweight copy variants for this NovaMind campaign topic: {topic}\n\n"
            "Use the existing core content below as context, but do not regenerate the full package.\n"
            f"{core_content}\n\n"
            "Return only the fields required by the JSON schema.\n\n"
            "Variant requirements:\n"
            "- Avoid generic marketing cliches and vague hype.\n"
            "- Avoid repeating the exact topic phrase awkwardly.\n"
            "- Make variants meaningfully different in angle, not minor wording changes.\n"
            "- Vary framing across workflow efficiency, growth outcomes, speed/productivity, and client delivery clarity.\n"
            "- Keep every option practical, specific, and submission-ready."
        )

    def _blog_schema(self) -> dict:
        """Return the small structured output schema for blog generation."""
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["blog_title", "blog_draft"],
            "properties": {
                "blog_title": {"type": "string"},
                "blog_draft": {"type": "string"},
            },
        }

    def _newsletter_schema(self) -> dict:
        """Return the small structured output schema for newsletter generation."""
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["newsletters"],
            "properties": {
                "newsletters": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "persona",
                            "newsletter_version_id",
                            "subject_line",
                            "preview_text",
                            "body",
                        ],
                        "properties": {
                            "persona": {"type": "string", "enum": PERSONAS},
                            "newsletter_version_id": {"type": "string"},
                            "subject_line": {"type": "string"},
                            "preview_text": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    },
                },
            },
        }

    def _variant_schema(self) -> dict:
        """Return the small structured output schema for second-pass copy variants."""
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["blog_title_variants", "newsletter_variants"],
            "properties": {
                "blog_title_variants": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {"type": "string"},
                },
                "newsletter_variants": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "persona",
                            "subject_line_variants",
                            "preview_text_variants",
                            "body_angle_variant",
                        ],
                        "properties": {
                            "persona": {"type": "string", "enum": PERSONAS},
                            "subject_line_variants": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {"type": "string"},
                            },
                            "preview_text_variants": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {"type": "string"},
                            },
                            "body_angle_variant": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["angle", "body"],
                                "properties": {
                                    "angle": {"type": "string"},
                                    "body": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        }
