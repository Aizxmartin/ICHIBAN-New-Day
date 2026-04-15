from __future__ import annotations


def validate_intake(session_state) -> tuple[bool, list[str]]:
    """Basic guardrail for early app wiring.

    Module 2 mainly needs a subject property PDF. Other modules can extend this later.
    """
    issues: list[str] = []

    if "subject_property_pdf" not in session_state:
        issues.append("Subject property PDF has not been uploaded.")

    return len(issues) == 0, issues
