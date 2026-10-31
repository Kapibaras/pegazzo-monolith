from enum import StrEnum


class DocumentType(StrEnum):
    """Enum for document type identifiers."""

    CIRCULATION_CARD = "circulation_card"
    INSURANCE_POLICY = "insurance_policy"
    INVOICE = "invoice"
    CREDIT_CONTRACT = "credit_contract"
    AMORTIZATION_TABLE = "amortization_table"
    PLATES = "plates"
    INE = "ine"
    DRIVER_LICENSE = "driver_license"
    CONTRACT = "contract"
    PROMISSORY_NOTE = "promissory_note"
    PROOF_OF_ADDRESS = "proof_of_address"
    UNKNOWN = "unknown"


class DocumentCategory(StrEnum):
    """Enum for document ownership category (derived by the backend)."""

    PEGAZZO = "PEGAZZO"
    PEGAZZO_ASSOCIATE = "PEGAZZO_ASSOCIATE"
    THIRD_PARTY = "THIRD_PARTY"
    UNCLASSIFIED = "UNCLASSIFIED"


class DocumentAnalysisStatus(StrEnum):
    """Enum for document analysis lifecycle status.

    Status machine:
        not_analyzed → pending → processing → valid | review | rejected | failed
        review → accepted | rejected
        valid | accepted | rejected → superseded (when replaced by a newer document)
    Transitions are enforced by the analysis service (PGZ-124).
    """

    NOT_ANALYZED = "not_analyzed"
    PENDING = "pending"
    PROCESSING = "processing"
    VALID = "valid"
    REVIEW = "review"
    REJECTED = "rejected"
    FAILED = "failed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"


class DocumentErrorReason(StrEnum):
    """Enum for document analysis error reasons."""

    LOW_RESOLUTION = "low_resolution"
    BLURRY = "blurry"
    TOO_DARK = "too_dark"
    TOO_BRIGHT = "too_bright"
    UNREADABLE = "unreadable"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    STUCK = "stuck"
    WRONG_DOCUMENT = "wrong_document"
