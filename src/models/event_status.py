from enum import StrEnum


class EventStatus(StrEnum):
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATED = "duplicated"
