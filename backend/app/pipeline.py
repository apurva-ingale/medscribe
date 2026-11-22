import logging
from pathlib import Path

from .db import SessionLocal
from .models import Consultation
from .notes import generate_note
from .transcription import preprocess, transcribe
from .validation import validate_note
from .ws import hub

log = logging.getLogger("pipeline")


def run_pipeline(cid: str) -> None:
    db = SessionLocal()
    c = db.get(Consultation, cid)
    try:
        def step(stage: str, **extra):
            c.status, c.stage = "processing", stage
            db.commit()
            hub.publish(cid, {"status": "processing", "stage": stage, **extra})

        step("preprocessing")
        wav = str(Path(c.audio_path).with_name(f"{cid}.16k.wav"))
        preprocess(c.audio_path, wav)

        step("transcribing")
        c.transcript = transcribe(wav)
        db.commit()
        step("generating", transcript=c.transcript)

        note = generate_note(c.transcript)
        step("validating")
        flags = validate_note(note, c.transcript)

        c.note = note.model_dump()
        c.flags = [f.model_dump() for f in flags]
        c.status, c.stage = "review", "ready"
        db.commit()
        hub.publish(cid, {"status": "review", "stage": "ready"})
    except Exception as e:  # surface any failure to the user instead of hanging
        log.exception("pipeline failed")
        db.rollback()
        c.status, c.error = "failed", str(e)[:500]
        db.commit()
        hub.publish(cid, {"status": "failed", "stage": "", "error": c.error})
    finally:
        db.close()
