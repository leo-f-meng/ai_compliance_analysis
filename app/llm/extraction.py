from tenacity import retry, stop_after_attempt, wait_exponential
from ..schema.schemas import ExtractionResult

from app.llm.client import client, MODEL


class LLMError(RuntimeError):
    pass


SYSTEM_PROMPT = """
You are an information extraction engine.
Return ONLY valid JSON. No markdown, no code fences, no commentary.

You will be given:
1) USER_INPUT (the raw text)
2) CONTEXT_SNIPPETS (retrieved chunks with ids)

You MUST follow:
- Use CONTEXT_SNIPPETS as the primary source of truth.
- Do NOT invent facts. If not supported by context or input, use null/unknown.
- Produce citations referencing chunk ids you used.
- citations must be a list of objects: { "doc_id": "...", "chunk_id": "...", "chunk_index": number }

Schema:
{
  "entity_type": "company" | "individual" | "unknown",
  "entity_name": string,
  "location": string | null,
  "people": string[],
  "intent": string | null,
  "risk_flags": string[],
  "risk_score": integer (0..10),
  "summary": string,
  "citations": [{"doc_id": string, "chunk_id": string, "chunk_index": integer}]
}
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
def llm_reasoning(
    user_text: str, contexts: list[dict] | None = None
) -> tuple[dict, dict | None]:

    combined_user = f"""USER_INPUT:{user_text}"""

    if contexts:
        context_block = "\n\n".join(
            [
                f"[doc_id={c['doc_id']} chunk_id={c['chunk_id']} chunk_index={c['chunk_index']}]\n{c['content']}"
                for c in contexts
            ]
        )

        combined_user = f"""{combined_user}
            CONTEXT_SNIPPETS:
            {context_block}
            """

    resp = client.responses.parse(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": combined_user},
        ],
        text_format=ExtractionResult,
    )
    data = resp.output_parsed
    if data is None:
        raise LLMError("No parsed output (model may have refused or output was empty).")

    usage = resp.model_dump().get("usage") or {}
    print("input_tokens: ", usage.get("input_tokens"))
    print("output_tokens: ", usage.get("output_tokens"))
    print("total_tokens: ", usage.get("total_tokens"))

    total_usage = {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }

    return data.model_dump(), total_usage
