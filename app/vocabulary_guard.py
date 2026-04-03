import re

_FORBIDDEN = re.compile(
    r"\b(compliant|compliance|legal|legally|valid|validity|approved|approval)\b",
    re.IGNORECASE,
)

# "compliance" is in the forbidden list because we never want the LLM to assert
# "this is in compliance with GDPR" — only humans can make that determination.
# Note: the word "compliance" in our own system prompt/UI strings is fine;
# this guard applies only to LLM-generated output text.


class VocabularyViolationError(ValueError):
    pass


def check_vocabulary(text: str) -> None:
    """Raise VocabularyViolationError if LLM output contains forbidden legal assertions."""
    match = _FORBIDDEN.search(text)
    if match:
        raise VocabularyViolationError(
            f"LLM output contains forbidden word '{match.group()}'. "
            "The system must not assert legal compliance — only humans can do that."
        )
