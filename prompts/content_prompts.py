"""Prompt builders used by the content generation service."""

from __future__ import annotations

from textwrap import dedent


def build_content_prompt(topic: str) -> str:
    """Return the prompt for the primary content generation call."""
    return dedent(
        f"""
        You are a content strategist for NovaMind, an AI startup serving small creative agencies.
        Write like a content and growth analyst preparing practical campaign assets, not like a software demo.

        Create campaign content for this topic: "{topic}".

        Requirements:
        - Return a JSON object only.
        - Include keys: blog_title_options, selected_blog_title, outline_options, selected_outline_id, blog_draft, newsletters.
        - blog_title_options must be a list of exactly 3 title strings.
        - selected_blog_title must be one of the blog_title_options.
        - outline_options must be a list of exactly 2 objects.
        - Each outline option must have keys: outline_id and items.
        - Each outline items list must contain 4 to 6 bullet items.
        - selected_outline_id must match one outline_id.
        - blog_draft should be 400 to 600 words.
        - newsletters must be a list of exactly 3 objects.
        - Each newsletter object must have keys:
          persona, newsletter_version_id,
          subject_line_options, selected_subject_line,
          preview_text_options, selected_preview_text,
          body_options, selected_body_angle, selected_body.
        - subject_line_options must include exactly 2 strings.
        - preview_text_options must include exactly 2 strings.
        - body_options must include exactly 2 objects with keys: angle and body.
        - selected_body_angle must match one body_options angle.
        - selected_body must match the body selected for sending.
        - The tone should feel credible for B2B marketing aimed at small agency decision-makers and practitioners.
        - Mention concrete outcomes such as lead response speed, content throughput, client communication, reporting, or utilization.
        - Personas must be:
          1. Creative Agency Owner
          2. Operations Manager at a Small Agency
          3. Freelance Creative Professional
        - Tailor each newsletter to the pain points and priorities of that persona.
        """
    ).strip()
