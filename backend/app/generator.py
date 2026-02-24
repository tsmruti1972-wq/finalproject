import os
import re
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


REQUIRED_HEADINGS = [
    "Key insights",
    "Drivers and impacts",
    "Assumptions made",
    "Risks and uncertainties",
    "Suggested follow up questions",
]


def _task_label(task_type: str) -> str:
    mapping = {
        "variance_explanation": "Variance explanation",
        "executive_narrative": "Executive narrative",
        "assumption_risk_check": "Assumption and risk check",
    }
    return mapping.get(task_type, task_type)


def _format_docs(retrieved_docs: list[dict[str, Any]]) -> str:
    lines = []
    for i, doc in enumerate(retrieved_docs, start=1):
        lines.append(f"[Doc {i}] {doc['title']} (id={doc['id']})")
        lines.append(doc["text"])
        lines.append("")
    return "\n".join(lines)


def build_prompt(
    task_type: str,
    user_message: str,
    context_assumptions: str,
    csv_rows: list[dict[str, Any]],
    retrieved_docs: list[dict[str, Any]],
) -> tuple[str, str]:
    csv_excerpt = "\n".join(str(r) for r in csv_rows[:15]) if csv_rows else "No CSV data provided"
    system_prompt = (
        "You are Financial Decision Support Copilot for senior financial analysts. "
        "This is decision support only, not forecasting.\n"
        "Use only user inputs and retrieved documents. If support is missing, say you cannot conclude and ask clarifying questions.\n"
        "Use conservative finance tone. Do not fabricate numbers. No definitive claims without support. "
        "Separate facts from assumptions.\n"
        "Include bracket citations like [Doc 1].\n"
        "Return these exact headings in this order:\n"
        "Key insights\nDrivers and impacts\nAssumptions made\nRisks and uncertainties\nSuggested follow up questions\n"
        "Then append Sources used with cited doc titles only."
    )

    user_prompt = (
        f"Task: {_task_label(task_type)}\n\n"
        f"User message:\n{user_message}\n\n"
        f"Context and assumptions:\n{context_assumptions or 'None provided'}\n\n"
        f"Parsed CSV content (sample):\n{csv_excerpt}\n\n"
        f"Retrieved documents:\n{_format_docs(retrieved_docs)}"
    )
    return system_prompt, user_prompt


def _extract_doc_refs(text: str) -> set[int]:
    return {int(m.group(1)) for m in re.finditer(r"\[Doc\s+(\d+)\]", text)}


def _ensure_template(text: str, retrieved_docs: list[dict[str, Any]]) -> str:
    output = text.strip()
    for heading in REQUIRED_HEADINGS:
        if heading not in output:
            output += f"\n\n{heading}\n- Unable to generate this section from available evidence."

    if "Sources used" not in output:
        refs = sorted(_extract_doc_refs(output))
        lines = ["Sources used"]
        for ref in refs:
            idx = ref - 1
            if 0 <= idx < len(retrieved_docs):
                lines.append(f"- [Doc {ref}] {retrieved_docs[idx]['title']}")
        if len(lines) == 1:
            lines.append("- No supporting sources cited")
        output += "\n\n" + "\n".join(lines)
    return output


def _fallback_response(
    task_type: str,
    user_message: str,
    context_assumptions: str,
    csv_rows: list[dict[str, Any]],
    retrieved_docs: list[dict[str, Any]],
) -> str:
    has_data = bool(csv_rows)
    docs_line = " ".join(f"[Doc {i}]" for i, _ in enumerate(retrieved_docs[:2], start=1)) or ""
    risk_gap = (
        "Missing numeric actual vs budget/prior rows in CSV input."
        if not has_data and task_type == "variance_explanation"
        else "No critical data gaps detected in provided inputs."
    )

    lines = [
        "Key insights",
        f"- Based on provided context, this is a {task_type.replace('_', ' ')} decision-support draft {docs_line}.".strip(),
        "- Evidence is limited to supplied inputs and retrieved policy/guidance excerpts.",
        "",
        "Drivers and impacts",
        "- Primary potential drivers should be validated against uploaded CSV line items before executive circulation.",
        "- Business impact statements are directional unless directly supported by provided figures.",
        "",
        "Assumptions made",
        f"- Assumed user focus from prompt: {user_message[:180]}",
        f"- Assumed context validity: {(context_assumptions[:180] or 'No additional assumptions provided.')}",
        "",
        "Risks and uncertainties",
        f"- {risk_gap}",
        "- Cannot conclude on unsupported claims; clarify timeframe, baseline, and materiality threshold.",
        "",
        "Suggested follow up questions",
        "- Which specific cost or revenue lines explain most of the variance?",
        "- Are one-time effects separated from run-rate effects?",
        "- Which assumptions are management-approved versus analyst-estimated?",
        "",
        "Sources used",
    ]

    refs = _extract_doc_refs("\n".join(lines))
    if refs:
        for ref in sorted(refs):
            idx = ref - 1
            if idx < len(retrieved_docs):
                lines.append(f"- [Doc {ref}] {retrieved_docs[idx]['title']}")
    else:
        lines.append("- No supporting sources cited")

    return "\n".join(lines)


def generate_response(
    task_type: str,
    user_message: str,
    context_assumptions: str,
    csv_rows: list[dict[str, Any]],
    retrieved_docs: list[dict[str, Any]],
) -> str:
    system_prompt, user_prompt = build_prompt(
        task_type=task_type,
        user_message=user_message,
        context_assumptions=context_assumptions,
        csv_rows=csv_rows,
        retrieved_docs=retrieved_docs,
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and OpenAI is not None:
        try:
            client = OpenAI(api_key=api_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            completion = client.chat.completions.create(
                model=model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            model_text = completion.choices[0].message.content or ""
            return _ensure_template(model_text, retrieved_docs)
        except Exception:
            # Gracefully degrade to the local grounded fallback when the external model
            # is unavailable (quota, rate limit, transient network, etc.).
            pass

    fallback = _fallback_response(task_type, user_message, context_assumptions, csv_rows, retrieved_docs)
    return _ensure_template(fallback, retrieved_docs)
