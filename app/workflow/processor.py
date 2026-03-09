import os
import time
import logging
from sqlalchemy import select

from app.workflow.pricing import estimate_cost_usd_micros
from app.workflow.risk import calculate_risk

from app.llm.extraction import llm_reasoning

from ..rag.rag_query import query_chunks

from ..schema.schemas import ExtractionResult

from app.db.database import SessionLocal
from app.db.models import Run
from app.logging_conf import setup_logging


def process_run_in_background(run_id, rag_enabled=True):
    setup_logging()
    logger = logging.getLogger("flowmind")

    start = time.time()
    db = SessionLocal()
    try:
        # 1) load run
        run = db.get(Run, run_id)
        if not run:
            logger.error(f"background run failed to find run_id={run_id}")
            return
        run.status = "processing"
        db.commit()

        # 2) LLM extract
        if rag_enabled:
            contexts = query_chunks(run.input_text, top_k=5)
            raw, usage = llm_reasoning(run.input_text, contexts)
        else:
            raw, usage = llm_reasoning(run.input_text)

        # Guardrail: ensure we always have a valid ExtractionResult
        result = ExtractionResult.model_validate(raw)

        # 3) deterministic risk
        new_score, new_flags = calculate_risk(
            result.entity_type, result.location, run.input_text
        )
        result.risk_score = new_score
        result.risk_flags = list(dict.fromkeys((result.risk_flags or []) + new_flags))

        # 4) metrics
        latency_ms = int((time.time() - start) * 1000)
        input_tokens = usage["input_tokens"] if usage else None
        output_tokens = usage["output_tokens"] if usage else None
        total_tokens = usage["total_tokens"] if usage else None
        cost_micros = estimate_cost_usd_micros(input_tokens, output_tokens)

        # 5) persist
        run.status = "done"
        run.result_json = result.model_dump()
        run.latency_ms = latency_ms
        run.model = os.getenv("OPEN_AI_MODEL", "gpt-5-nano")
        run.input_tokens = input_tokens
        run.output_tokens = output_tokens
        run.total_tokens = total_tokens
        run.cost_usd_micros = cost_micros
        run.error = None

        db.commit()

        return result

    except Exception as e:
        db.rollback()
        # record failure in run
        try:
            run = db.execute(select(Run).where(Run.id == run_id)).scalar_one()
            run.status = "failed"
            run.error = str(e)
            run.latency_ms = int((time.time() - start) * 1000)
            db.commit()
        except Exception:
            db.rollback()
        logger.exception(f"background run failed run_id={run_id}")
    finally:
        db.close()
