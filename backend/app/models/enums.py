from enum import StrEnum


class Role(StrEnum):
    INSTITUTION = "INSTITUTION"
    SCRUTINY_OFFICER = "SCRUTINY_OFFICER"
    REGIONAL_OFFICER = "REGIONAL_OFFICER"
    BUREAU_OFFICER = "BUREAU_OFFICER"
    ADMIN = "ADMIN"


def values(e: type[StrEnum]) -> str:
    return ",".join(f"'{m.value}'" for m in e)


class ObligationType(StrEnum):
    DOCUMENT_EXPIRY = "DOCUMENT_EXPIRY"
    UNDERTAKING = "UNDERTAKING"
    FDR_MATURITY = "FDR_MATURITY"
    EVC_VISIT = "EVC_VISIT"
    STAGE_SLA = "STAGE_SLA"
    COMPLAINT_SLA = "COMPLAINT_SLA"
    CUSTOM = "CUSTOM"


class ObligationStatus(StrEnum):
    UPCOMING = "UPCOMING"
    DUE_SOON = "DUE_SOON"
    OVERDUE = "OVERDUE"
    FULFILLED = "FULFILLED"
    WAIVED = "WAIVED"
    PAUSED = "PAUSED"


class ObligationSource(StrEnum):
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"
    OCR_CONFIRMED = "OCR_CONFIRMED"


class NotificationChannel(StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
