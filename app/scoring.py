from app.models.domain import Finding, FindingStatus, Severity, RagScore
from app.config import Settings


def apply_confidence_floor(findings: list[Finding], confidence_floor: float) -> list[Finding]:
    """Force any finding below the confidence floor to Unclear."""
    result = []
    for f in findings:
        if f.confidence < confidence_floor:
            result.append(f.model_copy(update={"status": FindingStatus.UNCLEAR}))
        else:
            result.append(f)
    return result


def calculate_rag_score(findings: list[Finding], settings: Settings) -> RagScore:
    """
    Pure Python scoring. No LLM involved.
    Only counts findings where status is ABSENT or UNCLEAR (not PRESENT).
    """
    absent_critical = sum(
        1 for f in findings
        if f.severity == Severity.CRITICAL and f.status == FindingStatus.ABSENT
    )
    absent_high = sum(
        1 for f in findings
        if f.severity == Severity.HIGH and f.status == FindingStatus.ABSENT
    )
    absent_medium = sum(
        1 for f in findings
        if f.severity == Severity.MEDIUM and f.status == FindingStatus.ABSENT
    )
    unclear_count = sum(
        1 for f in findings if f.status == FindingStatus.UNCLEAR
    )
    unclear_critical = sum(
        1 for f in findings
        if f.severity == Severity.CRITICAL and f.status == FindingStatus.UNCLEAR
    )

    # RED conditions
    if absent_critical >= settings.red_threshold_critical:
        return RagScore.RED
    if absent_high >= settings.red_threshold_high:
        return RagScore.RED

    # AMBER conditions
    if absent_high >= settings.amber_threshold_high:
        return RagScore.AMBER
    if absent_medium >= settings.amber_threshold_medium:
        return RagScore.AMBER
    if unclear_count >= settings.amber_threshold_unclear:
        return RagScore.AMBER
    if unclear_critical >= 1:
        return RagScore.AMBER

    return RagScore.GREEN
