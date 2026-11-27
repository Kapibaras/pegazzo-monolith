"""Prompt builder of the extraction service.

The declared type is only a hint: the model always reports the type it sees (``detected_type``), the issuing state
and where the expiry comes from (``expiry_source``), and fills the fields of the declared type.
"""

from typing import Any

from app.documents.extraction.errors import ExtractionError
from app.documents.registry import get_all_specs, get_doc_type_spec
from app.enum.document import DocumentType, ExpirySource

UNKNOWN_TYPE = DocumentType.UNKNOWN.value


def taxonomy() -> list[str]:
    """Return every value ``detected_type`` may take (all document types, ``unknown`` last)."""
    return [t.value for t in DocumentType if t != DocumentType.UNKNOWN] + [UNKNOWN_TYPE]


def extraction_spec(declared_type: str) -> dict[str, Any]:
    """Return the definition of *declared_type*, or raise ``ExtractionError`` when it has no fields to extract."""
    spec = get_doc_type_spec(declared_type)
    if spec is None or not spec.get("ai_analyzable") or not spec.get("fields"):
        msg = f"Document type '{declared_type}' has no extraction definition"
        raise ExtractionError(msg)
    return spec


def _taxonomy_lines() -> str:
    specs = get_all_specs()
    lines = [f"- {name}: {specs[name]['label_es']}" for name in taxonomy() if name in specs]
    lines.append(f"- {UNKNOWN_TYPE}: none of the above")
    return "\n".join(lines)


def build_prompt(declared_type: str, file_count: int = 1) -> str:
    """Build the extraction prompt for *declared_type* and *file_count* files of the same document."""
    spec = extraction_spec(declared_type)
    label = spec.get("document_label") or spec["label_es"]
    expected = spec.get("expected_doc_type")
    expiry_field = spec.get("expiry_field")

    files_note = (
        f"The {file_count} attached files are parts of the same document (for example the front and the back); "
        "read all of them together.\n"
        if file_count > 1
        else ""
    )
    title_note = f"Its printed title usually contains '{expected}'.\n" if expected else ""
    expiry_note = (
        f"For this type the expiry is read from the field '{expiry_field}'.\n"
        if expiry_field
        else "This type usually has no printed expiry.\n"
    )
    extra = spec.get("extra_instructions")
    extra_block = f"Document notes: {extra}\n" if extra else ""
    field_lines = "\n".join(f"- {name}: {meaning}" for name, meaning in spec["fields"].items())

    return (
        f"The user declared this document as: {label} ('{declared_type}'). The declaration may be wrong.\n"
        f"{title_note}"
        f"{files_note}"
        "Return ONLY a JSON object that follows the response schema.\n\n"
        "1. detected_type: the type you actually see, one of:\n"
        f"{_taxonomy_lines()}\n"
        "Use 'unknown' when it is not one of these types. Report it even when it differs from the declared type.\n"
        "2. issuing_state: the Mexican state (or authority) that issued the document, as printed; null if not shown.\n"
        f"3. expiry_source: '{ExpirySource.PRINTED}' when the document prints an expiry or validity end; "
        f"'{ExpirySource.RULE}' when it prints none but this kind of document expires; "
        f"'{ExpirySource.NONE}' when it does not expire.\n"
        f"{expiry_note}"
        "4. fields: the fields below, read from the document.\n"
        "5. unreadable_fields: the names of the fields that ARE printed on the document but you cannot read reliably "
        "(blurry, cut, covered, glare). Their value must be null.\n\n"
        "Rules:\n"
        "- Copy values exactly as printed. The document may be rotated; read it in whatever orientation it appears.\n"
        "- Use null when a field is not printed on the document; do not list it in unreadable_fields.\n"
        "- Use null and list the field in unreadable_fields when it is printed but not legible.\n"
        "- Never invent, compute or infer dates: only copy dates that are printed.\n"
        "- Never guess or copy a value from another field to fill an empty one.\n"
        f"{extra_block}\n"
        f"Field meanings:\n{field_lines}\n"
    )
