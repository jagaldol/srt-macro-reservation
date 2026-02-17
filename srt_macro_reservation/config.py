import os

from pydantic import BaseModel, Field, field_validator, model_validator


class SRTConfig(BaseModel):
    start_hotkey: str = Field("f9", description="매크로 시작 단축키")
    stop_hotkey: str = Field("esc", description="매크로 중지 단축키")
    image_match_confidence: float = Field(
        0.88,
        ge=0.4,
        le=0.99,
        description="이미지 인식 confidence",
    )
    enable_waiting_list: bool = Field(
        True,
        description="예약대기(신청하기) 자동 시도 여부",
    )
    roi_enabled: bool = Field(
        True,
        description="저장된 결과 영역(ROI) 사용 여부",
    )
    reservation_scan_timeout_sec: float = Field(
        5.0,
        ge=0.5,
        le=15.0,
        description="조회 직후 예약 탐색 최대 시간(초)",
    )
    refresh_settle_delay_sec: float = Field(
        0.18,
        ge=0.05,
        le=2.0,
        description="조회 클릭 후 결과 렌더링 대기 시간(초)",
    )
    enable_telegram_notification: bool = Field(
        False,
        description="텔레그램 알림 사용 여부",
    )
    telegram_bot_token: str | None = Field(
        None,
        description="텔레그램 봇 토큰",
    )
    telegram_chat_id: str | None = Field(
        None,
        description="텔레그램 채팅 ID",
    )

    @field_validator("start_hotkey", "stop_hotkey")
    @classmethod
    def validate_hotkey(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("단축키는 비어 있을 수 없습니다.")
        return normalized

    @model_validator(mode="after")
    def validate_config(self):
        if self.start_hotkey == self.stop_hotkey:
            raise ValueError("시작/중지 단축키는 서로 달라야 합니다.")
        if self.enable_telegram_notification:
            if not self.telegram_bot_token:
                raise ValueError("텔레그램 알림을 켠 경우 telegram_bot_token이 필요합니다.")
            if not self.telegram_chat_id:
                raise ValueError("텔레그램 알림을 켠 경우 telegram_chat_id가 필요합니다.")
        return self


def _parse_bool_env(key: str, default: bool) -> bool:
    raw_value = os.getenv(key)
    if raw_value is None or not raw_value.strip():
        return default

    lowered = raw_value.strip().lower()
    if lowered in {"1", "true", "t", "y", "yes"}:
        return True
    if lowered in {"0", "false", "f", "n", "no"}:
        return False
    raise ValueError(f"{key} 환경변수는 true/false 중 하나여야 합니다.")


def _parse_float_env(key: str, default: float) -> float:
    raw_value = os.getenv(key)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{key} 환경변수는 숫자여야 합니다.") from exc


def _parse_str_env(key: str, default: str) -> str:
    raw_value = os.getenv(key)
    if raw_value is None:
        return default
    stripped = raw_value.strip()
    return stripped if stripped else default


def _parse_optional_str_env(key: str) -> str | None:
    raw_value = os.getenv(key)
    if raw_value is None:
        return None
    stripped = raw_value.strip()
    return stripped if stripped else None


def load_config_from_env() -> SRTConfig:
    """환경변수에서 설정 값을 읽어와 SRTConfig 생성."""

    return SRTConfig(
        start_hotkey=_parse_str_env("START_HOTKEY", "f9"),
        stop_hotkey=_parse_str_env("STOP_HOTKEY", "esc"),
        image_match_confidence=_parse_float_env("IMAGE_MATCH_CONFIDENCE", 0.88),
        enable_waiting_list=_parse_bool_env("ENABLE_WAITING_LIST", True),
        roi_enabled=_parse_bool_env("ROI_ENABLED", True),
        reservation_scan_timeout_sec=_parse_float_env("RESERVATION_SCAN_TIMEOUT_SEC", 5.0),
        refresh_settle_delay_sec=_parse_float_env("REFRESH_SETTLE_DELAY_SEC", 0.18),
        enable_telegram_notification=_parse_bool_env("ENABLE_TELEGRAM_NOTIFICATION", False),
        telegram_bot_token=_parse_optional_str_env("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_parse_optional_str_env("TELEGRAM_CHAT_ID"),
    )
