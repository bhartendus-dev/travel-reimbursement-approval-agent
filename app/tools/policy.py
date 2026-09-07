import re

from app.services.policy_retriever import retrieve_policy


def _parse_limit(section_text: str) -> float | None:
    match = re.search(
        r"(?:Maximum reimbursable amount|Maximum).*?INR\s*([\d,]+)",
        section_text,
        flags=re.I | re.S,
    )
    return float(match.group(1).replace(",", "")) if match else None


def _parse_receipt_rule(section_text: str) -> str:
    if "Receipt is mandatory." in section_text:
        return "MANDATORY"

    threshold_match = re.search(
        r"receipt is mandatory when .*? exceeds INR\s*([\d,]+)",
        section_text,
        flags=re.I,
    )
    if threshold_match:
        threshold = float(threshold_match.group(1).replace(",", ""))
        return f"MANDATORY_ABOVE:{threshold}"

    return "OPTIONAL"


def get_policy_context(category: str, description: str | None = None) -> dict:
    if category == "OTHER":
        query = f"general unsupported expense category {description or ''}"
    else:
        query = f"domestic {category.lower()} reimbursement {description or ''}"

    retrieved = retrieve_policy(query, top_k=2)

    if not retrieved:
        return {
            "found": False,
            "eligible": False,
            "policy_id": "UNKNOWN",
            "section": "UNKNOWN",
            "max_amount": None,
            "receipt_rule": "OPTIONAL",
            "text": None,
            "retrieval_score": 0.0,
            "retrieved_chunks": [],
        }

    primary = retrieved[0]

    # Unsupported category must resolve to the general rule.
    if category == "OTHER":
        general = next(
            (item for item in retrieved if item["section"] == "GENERAL-01"),
            primary,
        )
        return {
            "found": True,
            "eligible": False,
            "policy_id": general["policy_id"],
            "section": general["section"],
            "max_amount": 0.0,
            "receipt_rule": "NOT_APPLICABLE",
            "text": general["text"],
            "retrieval_score": general["retrieval_score"],
            "retrieved_chunks": retrieved,
        }

    expected_prefix = f"{category}-"
    relevant = next(
        (
            item for item in retrieved
            if item["section"].startswith(expected_prefix)
        ),
        None,
    )

    if relevant is None:
        return {
            "found": False,
            "eligible": False,
            "policy_id": primary["policy_id"],
            "section": primary["section"],
            "max_amount": None,
            "receipt_rule": "OPTIONAL",
            "text": primary["text"],
            "retrieval_score": primary["retrieval_score"],
            "retrieved_chunks": retrieved,
        }

    return {
        "found": True,
        "eligible": True,
        "policy_id": relevant["policy_id"],
        "section": relevant["section"],
        "max_amount": _parse_limit(relevant["text"]),
        "receipt_rule": _parse_receipt_rule(relevant["text"]),
        "text": relevant["text"],
        "retrieval_score": relevant["retrieval_score"],
        "retrieved_chunks": retrieved,
    }
