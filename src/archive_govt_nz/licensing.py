"""Fail-closed dependency licence decisions with explicit alternatives."""

DENIED_LICENCE_TERMS = (
    "affero",
    "gnu general public license",
    "unknown",
)

# pip-licenses aggregates every Trove classifier into one semicolon-separated
# value. text-unidecode 1.3 also declares "License: Artistic License" as its
# primary package metadata, so this repository explicitly selects that offered
# alternative. This is intentionally package-specific, not a general rule that
# a permissive phrase erases a copyleft classifier.
SELECTED_LICENCE_ALTERNATIVES = {
    "text-unidecode": "artistic license",
}


def licence_denial(name: str, licence: str) -> str | None:
    """Return a denial reason unless an explicit offered alternative is selected."""
    normalized_name = name.casefold()
    normalized_licence = licence.casefold()
    denied_terms = tuple(
        term for term in DENIED_LICENCE_TERMS if term in normalized_licence
    )
    if not denied_terms:
        return None
    selected = SELECTED_LICENCE_ALTERNATIVES.get(normalized_name)
    if selected is not None and selected in normalized_licence:
        return None
    return ", ".join(denied_terms)
