import pytest
from app.encryption import generate_job_key, encrypt_excerpt, decrypt_excerpt


def test_encrypt_decrypt_roundtrip():
    key = generate_job_key()
    plaintext = "The processor shall notify within 72 hours of becoming aware of a breach."
    ciphertext = encrypt_excerpt(plaintext, key)
    assert ciphertext != plaintext
    result = decrypt_excerpt(ciphertext, key)
    assert result == plaintext


def test_different_keys_produce_different_ciphertext():
    key1 = generate_job_key()
    key2 = generate_job_key()
    text = "Test clause excerpt."
    assert encrypt_excerpt(text, key1) != encrypt_excerpt(text, key2)


def test_excerpt_truncated_to_500_chars():
    key = generate_job_key()
    long_text = "x" * 600
    ciphertext = encrypt_excerpt(long_text, key)
    decrypted = decrypt_excerpt(ciphertext, key)
    assert len(decrypted) == 500


def test_decrypt_with_wrong_key_raises():
    key1 = generate_job_key()
    key2 = generate_job_key()
    ciphertext = encrypt_excerpt("secret", key1)
    with pytest.raises(Exception):
        decrypt_excerpt(ciphertext, key2)


def test_empty_string_roundtrip():
    key = generate_job_key()
    ciphertext = encrypt_excerpt("", key)
    assert decrypt_excerpt(ciphertext, key) == ""
