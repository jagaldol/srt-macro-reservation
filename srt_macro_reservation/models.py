from dataclasses import dataclass
from enum import Enum
from pathlib import Path


Region = tuple[int, int, int, int]


class ScanPhase(Enum):
    REFRESH = "refresh"
    WAIT_CONNECTION = "wait_connection"
    RESERVATION = "reservation"


class RefreshOutcome(Enum):
    NOT_FOUND = "not_found"
    WAIT_CONNECTION = "wait_connection"
    READY = "ready"


@dataclass(frozen=True)
class TemplateSet:
    booking: Path | None
    waiting: Path | None
    refresh: Path | None
    sold_out: Path | None
    connection_wait: Path | None
