import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from db.models import insert_email, update_company_status, log_event

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

SENDER_NAME = os.getenv("SENDER_NAME", "Alex")
SENDER_TRADING_NAME = os.getenv("SENDER_TRADING_NAME", "Brightwick Digital")
SENDER_ADDRESS = os.getenv("SENDER_ADDRESS", "123 Example Street, Leeds, LS1 1AA")

_SECTOR_TONE = {
    "hospitality": "warm and conversational",
    "restaurant": "warm and conversational",
    "hotel": "warm and conversational",
    "pub": "warm and conversational",
    "bar": "warm and conversational",
    "cafe": "warm and conversational",
    "plumber": "direct and practical",
    "electrician": "direct and practical",
    "builder": "direct and practical",
    "tradesman": "direct and practical",
    "roofer": "direct and practical",
    "carpenter": "direct and practical",
    "joiner": "direct and practical",
    "mechanic": "direct and practical",
    "garage": "direct and practical",
    "solicitor": "formal and professional",
    "accountant": "formal and professional",
    "legal": "formal and professional",
    "dental": "formal and professional",
    "medical": "formal and professional",
    "financial": "formal and professional",
    "insurance": "formal and professional",
    "consultant": "formal and professional",
}


def _infer_tone(sic_description: Optional[str]) -> str:
    if not sic_description:
        return "professional and friendly"
    desc_lower = sic_description.lower()
    for keyword, tone in _SECTOR_TONE.items():
        if keyword in desc_lower:
            return tone
    return "professional and friendly"


def _format_address(registered_address: Optional[str]) -> str:
    if not registered_address:
        return ""
    try:
        addr = json.loads(registered_address) if isinstance(registered_address, str) else registered_address
        parts = [
            addr.get("address_line_1", ""),
            addr.get("address_line_2", ""),
            addr.get("locality", ""),
            addr.get("postal_code", ""),
            addr.get("country", ""),
        ]
        return ", ".join(p for p in parts if p)
    except Exception:
        return str(registered_address)


def _first_officer(officer_names_json: Optional[str]) -> str:
    if not officer_names_json:
        return "there"
    try:
        names = json.loads(officer_names_json) if isinstance(officer_names_json, str) else officer_names_json
        if names:
            full = names[0]
            first = full.split(",")[-1].strip().split()[0] if "," in full else full.split()[0]
            return first.title()
    except Exception:
        pass
    return "there"


def _build_prompt(company: dict, variant: int) -> str:
    company_name = company["company_name"]
    region = company.get("region") or "UK"
    sic_desc = company.get("sic_description") or ""
    weakness = company.get("weakness_summary") or "limited online presence"
    tone = _infer_tone(sic_desc)
    officer_first = _first_officer(company.get("officer_names"))
    incorporated = company.get("incorporated_date") or ""
    company_age = ""
    if incorporated:
        try:
            from datetime import date
            year = int(incorporated[:4])
            age = date.today().year - year
            company_age = f"established {age} years ago" if age > 0 else "recently established"
        except Exception:
            pass

    domain = company.get("discovered_domain") or "no website"

    if variant == 0:
        angle = "introduce the core problem (their weak online presence) and what you offer"
        word_limit = "80 words maximum for the body"
        subject_hint = "hint at improving their online visibility"
    elif variant == 1:
        angle = "take a different angle — focus on what competitors in their area are doing online that they aren't"
        word_limit = "100 words maximum for the body"
        subject_hint = "reference the competition or a local angle"
    else:
        angle = "send a final short message, create urgency, mention you're wrapping up outreach to this area"
        word_limit = "60 words maximum for the body"
        subject_hint = "create gentle urgency"

    return f"""You are writing a cold email on behalf of {SENDER_NAME} from {SENDER_TRADING_NAME}.

COMPANY DETAILS:
- Name: {company_name}
- Region: {region}
- Sector: {sic_desc or 'Unknown'}
- Age: {company_age or 'Unknown'}
- Online weakness: {weakness}
- Current domain: {domain}

TONE: {tone}
EMAIL ANGLE: {angle}
LENGTH: {word_limit}, subject line ≤8 words

MANDATORY RULES — every email MUST include ALL of these, no exceptions:
1. Address the recipient as "{officer_first}" (use first name only)
2. Sign off with "{SENDER_NAME}" from "{SENDER_TRADING_NAME}"
3. Include sender address on a new line at the bottom: {SENDER_ADDRESS}
4. Include this exact opt-out line as the last line: "If you'd prefer not to hear from us, reply with STOP and we'll remove you immediately."
5. Reference the specific weakness: {weakness}
6. Mention something local or specific to {region} or their sector ({sic_desc or 'their industry'})
7. Do NOT use jargon, buzzwords, or generic phrases like "I hope this finds you well"
8. Do NOT make promises you cannot keep
9. Body must be plain text, no HTML, no markdown

OUTPUT FORMAT (JSON only, no other text):
{{
  "subject": "...",
  "body": "..."
}}"""


class _GeminiError(Exception):
    pass


class _GroqError(Exception):
    pass


@retry(
    retry=retry_if_exception_type(_GeminiError),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
)
def _call_gemini(prompt: str) -> dict:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=512,
            ),
        )
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise _GeminiError(f"JSON parse failed: {exc}") from exc
    except Exception as exc:
        if "429" in str(exc) or "quota" in str(exc).lower() or "rate" in str(exc).lower():
            raise _GeminiError(f"Rate limit: {exc}") from exc
        raise _GeminiError(str(exc)) from exc


@retry(
    retry=retry_if_exception_type(_GroqError),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(3),
)
def _call_groq(prompt: str) -> dict:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You write cold emails. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        text = chat.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise _GroqError(f"JSON parse failed: {exc}") from exc
    except Exception as exc:
        if "429" in str(exc) or "rate" in str(exc).lower():
            raise _GroqError(f"Rate limit: {exc}") from exc
        raise _GroqError(str(exc)) from exc


def _generate_one(prompt: str) -> tuple[dict, str]:
    if GEMINI_API_KEY:
        try:
            result = _call_gemini(prompt)
            return result, "gemini"
        except Exception as exc:
            logger.warning("Gemini failed, falling back to Groq: %s", exc)

    if GROQ_API_KEY:
        result = _call_groq(prompt)
        return result, "groq"

    raise RuntimeError("No LLM API keys configured (GEMINI_API_KEY or GROQ_API_KEY)")


class EmailGenerator:
    def generate(self, company: dict) -> list[dict]:
        company_id = company["id"]
        results = []

        for variant in range(3):
            prompt = _build_prompt(company, variant)
            try:
                content, llm_used = _generate_one(prompt)
            except Exception as exc:
                logger.error(
                    "Failed to generate variant %d for company %d: %s",
                    variant,
                    company_id,
                    exc,
                )
                continue

            subject = content.get("subject", "").strip()
            body = content.get("body", "").strip()

            if not subject or not body:
                logger.warning("LLM returned empty subject/body for variant %d", variant)
                continue

            email_id = insert_email(
                company_id=company_id,
                variant=variant,
                subject=subject,
                body_text=body,
                llm_used=llm_used,
            )

            results.append({
                "email_id": email_id,
                "variant": variant,
                "subject": subject,
                "body_text": body,
                "llm_used": llm_used,
            })

        if results:
            update_company_status(company_id, "personalised")
            log_event(
                company_id,
                "personalise",
                f"generated {len(results)} variants via {results[0]['llm_used']}",
            )

        return results
