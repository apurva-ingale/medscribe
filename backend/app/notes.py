from google import genai
from google.genai import types
from pydantic import ValidationError

from .config import settings
from .schemas import ClinicalNote

SYSTEM = """You are a medical scribe. Convert the consultation transcript into a structured clinical note.
Rules:
- Use ONLY information explicitly stated in the transcript. Never infer diagnoses, doses, or values that were not said.
- Every item needs a short verbatim source_quote copied from the transcript.
- Put each fact in the correct section; use an empty list when a section was not discussed.
- Write concise clinical language. Keep drug names, doses and numbers exactly as spoken."""


def generate_note(transcript: str) -> ClinicalNote:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    client = genai.Client(api_key=settings.gemini_api_key)
    last: Exception | None = None
    for _ in range(2):
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=f"Consultation transcript:\n\n{transcript}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                response_mime_type="application/json",
                response_schema=ClinicalNote,
                temperature=0.1,
            ),
        )
        try:
            return ClinicalNote.model_validate_json(resp.text)
        except (ValidationError, ValueError) as e:
            last = e
    raise RuntimeError(f"Model returned an invalid note: {last}")
