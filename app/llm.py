import json
import os
from typing import Optional, Tuple, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI
from app.schemas import ExtractionResult


RAG_SYSTEM_PROMPT = """
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
  "jurisdiction": string | null,
  "people": string[],
  "intent": string | null,
  "risk_flags": string[],
  "risk_score": integer (0..10),
  "summary": string,
  "citations": [{"doc_id": string, "chunk_id": string, "chunk_index": integer}]
}
"""


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True
    )
    def extract_json(self, text: str) -> Tuple[dict, dict]:
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": "Extract structured fields from the user's text.",
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                text_format=ExtractionResult,
            )

            parsed = response.output_parsed
            if parsed is None:
                raise LLMError(
                    "No parsed output (model may have refused or output was empty)."
                )

            usage = response.model_dump().get("usage") or {}
            print("input_tokens: ", usage.get("input_tokens"))
            print("output_tokens: ", usage.get("output_tokens"))
            print("total_tokens: ", usage.get("total_tokens"))

            total_usage = {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }

            return parsed.model_dump(), total_usage

        except Exception as e:
            raise LLMError(str(e)) from e

    def extract_json_with_context(
        self, user_text: str, contexts: list[dict]
    ) -> tuple[dict, dict | None]:
        context_block = "\n\n".join(
            [
                f"[doc_id={c['doc_id']} chunk_id={c['chunk_id']} chunk_index={c['chunk_index']}]\n{c['content']}"
                for c in contexts
            ]
        )

        combined_user = f"""USER_INPUT:
            {user_text}
            CONTEXT_SNIPPETS:
            {context_block}
            """

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": combined_user},
            ],
            temperature=0.1,
        )

        content = (resp.choices[0].message.content or "").strip()
        if not content.startswith("{"):
            raise LLMError(f"Non-JSON output: {content[:200]}")

        data = json.loads(content)

        usage = None
        u = getattr(resp, "usage", None)
        if u is None:
            usage = None
        elif isinstance(u, dict):
            usage = {
                "input_tokens": u.get("prompt_tokens") or u.get("input_tokens"),
                "output_tokens": u.get("completion_tokens") or u.get("output_tokens"),
                "total_tokens": u.get("total_tokens"),
            }
        else:
            usage = {
                "input_tokens": getattr(u, "prompt_tokens", None)
                or getattr(u, "input_tokens", None),
                "output_tokens": getattr(u, "completion_tokens", None)
                or getattr(u, "output_tokens", None),
                "total_tokens": getattr(u, "total_tokens", None),
            }

        return data, usage
