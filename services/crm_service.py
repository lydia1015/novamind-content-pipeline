"""Brevo CRM integration for contact sync, segmentation, and newsletter sends."""

from __future__ import annotations

import json
from datetime import datetime

import requests
from requests import Response
from requests.exceptions import RequestException

from config import CAMPAIGN_LOGS_FILE, CONTACTS_FILE, PERSONAS, SEGMENT_DEFINITIONS_FILE, load_config
from services.campaign_logger import CampaignLogger


class CRMService:
    """Manage local contacts, sync them to Brevo, and send persona-based newsletters."""

    BASE_URL = "https://api.brevo.com/v3"
    REQUEST_TIMEOUT = 15

    def __init__(self) -> None:
        self.logger = CampaignLogger()
        self.config = load_config()

    def run_campaign(self, content: dict) -> dict:
        """Load contacts, sync them to Brevo, send persona-specific emails, and log campaign history."""
        contacts = self._load_contacts()
        segment_definitions = self._load_segment_definitions()
        newsletters_by_persona = {
            item["persona"]: item for item in content.get("newsletters", []) if item.get("persona")
        }
        send_date = datetime.utcnow().isoformat() + "Z"

        segments = {persona: [] for persona in PERSONAS}
        refreshed_contacts = []

        for contact in contacts:
            updated_contact = self._sync_contact(contact)
            refreshed_contacts.append(updated_contact)
            persona = updated_contact.get("persona")
            if persona in segments:
                segments[persona].append(updated_contact)

        self._save_contacts(refreshed_contacts)

        campaign_entries = []
        for persona, segment_contacts in segments.items():
            newsletter = newsletters_by_persona.get(persona, {})
            segment_definition = segment_definitions.get(persona, {})
            list_id = self._list_id_for_persona(persona)
            send_results = self._send_newsletter_batch(newsletter, segment_contacts)

            entry = {
                "campaign_id": f"campaign-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{persona.lower().split()[0]}",
                "blog_title": content.get("blog_title"),
                "persona": persona,
                "segment_name": segment_definition.get("segment_name", persona),
                "brevo_list_id": list_id,
                "newsletter_version_id": newsletter.get("newsletter_version_id", "newsletter-generic-v1"),
                "send_date": send_date,
                "total_contacts": len(segment_contacts),
                "contact_ids": [contact["id"] for contact in segment_contacts],
                "recipient_emails": [contact["email"] for contact in segment_contacts if contact.get("email")],
                "brevo_send_status": self._summarize_send_status(send_results, segment_contacts),
                "brevo_message_id": self._first_message_id(send_results),
            }
            self.logger.append_record(CAMPAIGN_LOGS_FILE, entry)
            campaign_entries.append(entry)

        return {
            "contacts": refreshed_contacts,
            "segments": segments,
            "campaign_entries": campaign_entries,
        }

    def _load_contacts(self) -> list:
        """Load local contacts from JSON storage."""
        try:
            with CONTACTS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_contacts(self, contacts: list) -> None:
        """Persist the updated contacts file."""
        with CONTACTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(contacts, file, indent=2)

    def _load_segment_definitions(self) -> dict:
        """Load local segment metadata used for campaign logging."""
        try:
            with SEGMENT_DEFINITIONS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return {item["persona"]: item for item in data if isinstance(item, dict) and item.get("persona")}
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}

    def _sync_contact(self, contact: dict) -> dict:
        """Normalize a contact, upsert it in Brevo, and add it to the persona-specific list."""
        normalized = dict(contact)
        normalized["persona"] = self._normalize_persona(contact.get("persona", ""))
        normalized["last_updated_at"] = datetime.utcnow().isoformat() + "Z"
        normalized["crm_status"] = "failed"

        email = normalized.get("email", "").strip()
        if not email:
            normalized["crm_error"] = "Missing contact email."
            return normalized

        list_id = self._list_id_for_persona(normalized["persona"])
        if not self._brevo_enabled():
            normalized["crm_error"] = "Brevo credentials or list mapping missing."
            return normalized

        try:
            response = self._upsert_contact_in_brevo(normalized, list_id)
            normalized["crm_status"] = "synced"
            normalized["brevo_contact_id"] = self._extract_contact_id(response)
            normalized["brevo_list_id"] = list_id
            normalized.pop("crm_error", None)
        except RequestException as exc:
            normalized["crm_error"] = str(exc)
        except ValueError as exc:
            normalized["crm_error"] = str(exc)

        return normalized

    def _normalize_persona(self, persona: str) -> str:
        """Ensure contacts always map into one of the supported personas."""
        for supported_persona in PERSONAS:
            if persona.strip().lower() == supported_persona.lower():
                return supported_persona
        return "Freelance Creative Professional"

    def _brevo_enabled(self) -> bool:
        """Return True only when the required Brevo configuration is present."""
        return bool(
            self.config.get("brevo_api_key")
            and self.config.get("brevo_sender_email")
            and self.config.get("brevo_sender_name")
        )

    def _build_headers(self) -> dict:
        """Build the shared Brevo headers used for every request."""
        return {
            "accept": "application/json",
            "api-key": self.config.get("brevo_api_key", ""),
            "content-type": "application/json",
        }

    def _list_id_for_persona(self, persona: str) -> str:
        """Map each persona to the correct Brevo list configured in environment variables."""
        mapping = {
            "Creative Agency Owner": self.config.get("brevo_list_id_owner", ""),
            "Operations Manager at a Small Agency": self.config.get("brevo_list_id_operations", ""),
            "Freelance Creative Professional": self.config.get("brevo_list_id_freelance", ""),
        }
        return mapping.get(persona, "")

    def _upsert_contact_in_brevo(self, contact: dict, list_id: str) -> Response:
        """
        Create or update a Brevo contact.

        Endpoint:
        POST /contacts

        Example payload shape:
        {
          "email": "maya@northstudioco.com",
          "attributes": {
            "FIRSTNAME": "Maya",
            "LASTNAME": "Patel",
            "COMPANY": "North Studio Co.",
            "JOBTITLE": "Founder",
            "PERSONA": "Creative Agency Owner"
          },
          "listIds": [101],
          "updateEnabled": true
        }
        """
        if not list_id:
            raise ValueError(f"Missing Brevo list ID for persona: {contact['persona']}")

        payload = {
            "email": contact["email"],
            "attributes": {
                "FIRSTNAME": contact.get("first_name", ""),
                "LASTNAME": contact.get("last_name", ""),
                "COMPANY": contact.get("company", ""),
                "JOBTITLE": contact.get("job_title", ""),
                "PERSONA": contact["persona"],
            },
            "listIds": [int(list_id)],
            "updateEnabled": True,
        }
        return self._post("/contacts", payload)

    def _add_contact_to_list(self, email: str, list_id: str) -> Response:
        """
        Ensure the contact is present in the correct Brevo list.

        Endpoint:
        POST /contacts/lists/{listId}/contacts/add

        Example payload shape:
        {
          "emails": ["maya@northstudioco.com"]
        }
        """
        if not list_id:
            raise ValueError("Cannot add contact to Brevo list without a configured list ID.")

        payload = {"emails": [email]}
        return self._post(f"/contacts/lists/{int(list_id)}/contacts/add", payload)

    def _send_newsletter_batch(self, newsletter: dict, contacts: list) -> list:
        """Send the persona-specific newsletter to each synced contact in the segment."""
        if not self._brevo_enabled():
            return []

        results = []
        for contact in contacts:
            email = contact.get("email", "").strip()
            if not email or contact.get("crm_status") != "synced":
                results.append({"email": email, "status": "skipped", "message_id": None})
                continue

            try:
                response = self._send_transactional_email(newsletter, contact)
                results.append(
                    {
                        "email": email,
                        "status": "sent",
                        "message_id": self._extract_message_id(response),
                    }
                )
            except RequestException:
                results.append({"email": email, "status": "failed", "message_id": None})

        return results

    def _send_transactional_email(self, newsletter: dict, contact: dict) -> Response:
        """
        Send a transactional email through Brevo.

        Endpoint:
        POST /smtp/email

        Example payload shape:
        {
          "sender": {"name": "NovaMind", "email": "marketing@novamind.ai"},
          "to": [{"email": "maya@northstudioco.com", "name": "Maya Patel"}],
          "subject": "Scale client delivery without adding headcount pressure",
          "htmlContent": "<p>...</p>"
        }
        """
        payload = {
            "sender": {
                "email": self.config.get("brevo_sender_email", ""),
                "name": self.config.get("brevo_sender_name", "NovaMind"),
            },
            "to": [
                {
                    "email": contact["email"],
                    "name": f"{contact.get('first_name', '').strip()} {contact.get('last_name', '').strip()}".strip(),
                }
            ],
            "subject": newsletter.get("subject_line", "NovaMind update"),
            "htmlContent": self._build_email_html(newsletter, contact),
        }
        return self._post("/smtp/email", payload)

    def _build_email_html(self, newsletter: dict, contact: dict) -> str:
        """Build a lightweight HTML email body for the newsletter send."""
        greeting_name = contact.get("first_name", "").strip() or "there"
        preview_text = newsletter.get("preview_text", "")
        body = newsletter.get("body", "")
        return (
            f"<html><body>"
            f"<p>Hi {greeting_name},</p>"
            f"<p><strong>{preview_text}</strong></p>"
            f"<p>{body}</p>"
            f"<p>Best,<br>{self.config.get('brevo_sender_name', 'NovaMind')}</p>"
            f"</body></html>"
        )

    def _post(self, path: str, payload: dict) -> Response:
        """Send a POST request to Brevo and raise a readable error on failure."""
        url = f"{self.BASE_URL}{path}"
        response = requests.post(
            url,
            headers=self._build_headers(),
            json=payload,
            timeout=self.REQUEST_TIMEOUT,
        )
        try:
            response.raise_for_status()
        except RequestException as exc:
            details = self._safe_error_message(response)
            raise RequestException(f"Brevo request failed for {path}: {details}") from exc
        return response

    def _extract_contact_id(self, response: Response) -> str | None:
        """Extract the Brevo contact ID when the API returns one."""
        try:
            payload = response.json()
        except ValueError:
            return None
        contact_id = payload.get("id")
        return str(contact_id) if contact_id is not None else None

    def _extract_message_id(self, response: Response) -> str | None:
        """Extract the transactional message ID from Brevo's response when present."""
        try:
            payload = response.json()
        except ValueError:
            return None
        message_id = payload.get("messageId")
        return str(message_id) if message_id is not None else None

    def _safe_error_message(self, response: Response) -> str:
        """Return a short readable error payload from a Brevo response."""
        try:
            payload = response.json()
            return payload.get("message") or json.dumps(payload)
        except ValueError:
            return response.text.strip() or f"HTTP {response.status_code}"

    def _summarize_send_status(self, send_results: list, contacts: list) -> str:
        """Collapse individual email results into a single campaign-level status."""
        if not contacts:
            return "skipped"
        if not send_results:
            return "not_sent"
        statuses = {item["status"] for item in send_results}
        if statuses == {"sent"}:
            return "sent"
        if "sent" in statuses and "failed" in statuses:
            return "partial"
        if "sent" in statuses and "skipped" in statuses:
            return "partial"
        if "failed" in statuses:
            return "failed"
        return "skipped"

    def _first_message_id(self, send_results: list) -> str | None:
        """Return the first available Brevo message ID for logging purposes."""
        for result in send_results:
            if result.get("message_id"):
                return result["message_id"]
        return None
