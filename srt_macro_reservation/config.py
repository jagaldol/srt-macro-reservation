import os
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SRTConfig(BaseModel):
    departure_station: str = Field(..., description="SRT 출발역", example="서울")
    arrival_station: str = Field(..., description="SRT 도착역", example="부산")
    departure_date: str = Field(..., description="출발 날짜 YYYYMMDD", example="20250101")
    departure_time: str = Field(..., description="출발 시간(짝수, hh 형식)", example="06")
    num_to_check: int = Field(3, ge=1, description="검색 결과 중 시도할 시간표 수")
    user_id: str = Field(..., description="사용자 ID", example="1234567890")
    password: str = Field(..., description="비밀번호", example="0000")

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

    return SRTConfig(
        departure_station=_get_env("DEPARTURE_STATION"),
        arrival_station=_get_env("ARRIVAL_STATION"),
        departure_date=_get_env("DEPARTURE_DATE"),
        departure_time=_get_env("DEPARTURE_TIME"),
        num_to_check=_parse_int_env("NUM_TO_CHECK", default_num),
        user_id=_get_env("USER_ID"),
        password=_get_env("PASSWORD"),
    )
