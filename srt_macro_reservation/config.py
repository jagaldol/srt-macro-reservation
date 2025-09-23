import os
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SRTConfig(BaseModel):
    departure_station: str = Field(..., description="SRT 출발역", example="서울")
    arrival_station: str = Field(..., description="SRT 도착역", example="부산")
    departure_date: str = Field(..., description="출발 날짜 YYYYMMDD", example="20250101")
    departure_time: str = Field(..., description="출발 시간(짝수, hh 형식)", example="06")
    num_to_check: int = Field(3, ge=1, description="검색 결과 중 시도할 시간표 수")
    num_to_skip: int = Field(0, ge=0, description="검색 결과에서 건너뛸 시간표 수")
    user_id: str = Field(..., description="사용자 ID", example="1234567890")
    password: str = Field(..., description="비밀번호", example="0000")
    enable_waiting_list: bool = Field(
        True,
        description="예약대기(신청하기) 자동 시도 여부",
        example=True,
    )

    @field_validator("departure_date")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y%m%d")
        except ValueError:
            raise ValueError("날짜가 잘못되었습니다. YYYYMMDD 형식으로 입력해주세요.")
        return value

    @field_validator("departure_time")
    def validate_time(cls, value):
        if not value.isnumeric() or int(value) % 2 != 0:
            raise ValueError("출발 시간은 짝수 시간 (hh 형식)으로 입력해야 합니다.")
        return value


def load_config_from_env() -> SRTConfig:
    """환경변수에서 설정 값을 읽어와 SRTConfig 생성."""

    def _get_env(key: str) -> str | None:
        value = os.getenv(key)
        if value is None:
            return None
        return value.strip()

    def _parse_int_env(key: str, default: int) -> int:
        raw_value = os.getenv(key)
        if raw_value is None or not raw_value.strip():
            return default
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{key} 환경변수는 정수여야 합니다.") from exc

    default_num = SRTConfig.model_fields["num_to_check"].default
    default_skip = SRTConfig.model_fields["num_to_skip"].default

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

    return SRTConfig(
        departure_station=_get_env("DEPARTURE_STATION"),
        arrival_station=_get_env("ARRIVAL_STATION"),
        departure_date=_get_env("DEPARTURE_DATE"),
        departure_time=_get_env("DEPARTURE_TIME"),
        num_to_check=_parse_int_env("NUM_TO_CHECK", default_num),
        num_to_skip=_parse_int_env("NUM_TO_SKIP", default_skip),
        user_id=_get_env("USER_ID"),
        password=_get_env("PASSWORD"),
        enable_waiting_list=_parse_bool_env("ENABLE_WAITING_LIST", True),
    )
