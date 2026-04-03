import pytest
from app.vocabulary_guard import check_vocabulary, VocabularyViolationError


def test_clean_text_passes():
    check_vocabulary("The clause is Present. Confidence: 0.92.")


def test_compliant_raises():
    with pytest.raises(VocabularyViolationError, match="compliant"):
        check_vocabulary("This contract is compliant with GDPR.")


def test_legal_raises():
    with pytest.raises(VocabularyViolationError, match="legal"):
        check_vocabulary("The clause is legally sufficient.")


def test_valid_raises():
    with pytest.raises(VocabularyViolationError, match="valid"):
        check_vocabulary("The DPA is valid under GDPR.")


def test_approved_raises():
    with pytest.raises(VocabularyViolationError, match="approved"):
        check_vocabulary("This document has been approved.")


def test_case_insensitive():
    with pytest.raises(VocabularyViolationError):
        check_vocabulary("The contract is COMPLIANT.")


def test_allowed_vocabulary():
    # These must not raise
    for word in ["present", "absent", "unclear", "needs review", "Present", "Absent"]:
        check_vocabulary(f"Status: {word}.")
