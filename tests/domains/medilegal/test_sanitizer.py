"""Tests for Medico-Legal anonymization and sanitization."""

from __future__ import annotations

from archive_govt_nz.domains.medilegal.sanitizer import (
    sanitize_medilegal_text,
    verify_sanitization,
)


def test_sanitize_medilegal_text_nhi() -> None:
    """Sanitizer redacts NHI numbers deterministically."""
    raw = "Patient with NHI ABC1234 presented to the emergency department."
    sanitized = sanitize_medilegal_text(raw)
    assert "ABC1234" not in sanitized
    assert "[REDACTED NHI]" in sanitized
    assert verify_sanitization(sanitized) is True


def test_sanitize_medilegal_text_contact() -> None:
    """Sanitizer redacts email, phone, and explicit date of birth values."""
    raw = "Contact details: dr.smith@clinic.co.nz or +64 21 123 4567, DOB: 14/05/1982."
    sanitized = sanitize_medilegal_text(raw)
    assert "dr.smith@clinic.co.nz" not in sanitized
    assert "[REDACTED EMAIL]" in sanitized
    assert "+64 21 123 4567" not in sanitized
    assert "[REDACTED PHONE]" in sanitized
    assert "DOB: [REDACTED DOB]" in sanitized


def test_verify_sanitization_detects_leak() -> None:
    """Verification fails if text contains unredacted patient NHI."""
    leaky = "Contains raw NHI XYZ9876."
    assert verify_sanitization(leaky) is False
