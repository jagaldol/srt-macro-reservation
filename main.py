import argparse
import os

import dotenv

from srt_macro_reservation.config import load_config_from_env
from srt_macro_reservation.srt_macro_agent import SRTMacroAgent


def _parse_bool_arg(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "t", "y", "yes"}:
        return True
    if lowered in {"0", "false", "f", "n", "no"}:
        return False
    raise argparse.ArgumentTypeError("true 또는 false 값을 전달해야 합니다.")


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SRT 이미지 매크로 실행 설정")
    parser.add_argument("--start-hotkey", help="매크로 시작 단축키 (예: f9)")
    parser.add_argument("--stop-hotkey", help="매크로 중지 단축키 (예: esc)")
    parser.add_argument("--image-match-confidence", type=float, help="이미지 인식 confidence (0.4~0.99)")
    parser.add_argument(
        "--enable-waiting-list",
        type=_parse_bool_arg,
        help="예약대기(신청하기) 자동 시도 여부 (true/false)",
    )
    parser.add_argument(
        "--roi-enabled",
        type=_parse_bool_arg,
        help="저장된 결과 영역(ROI) 사용 여부 (true/false)",
    )
    parser.add_argument(
        "--reservation-scan-timeout-sec",
        type=float,
        help="조회 직후 예약 탐색 최대 시간(초)",
    )
    parser.add_argument(
        "--refresh-settle-delay-sec",
        type=float,
        help="조회 버튼 클릭 후 결과 렌더링 대기 시간(초)",
    )
    parser.add_argument(
        "--enable-telegram-notification",
        type=_parse_bool_arg,
        help="텔레그램 알림 사용 여부 (true/false)",
    )
    parser.add_argument("--telegram-bot-token", help="텔레그램 봇 토큰")
    parser.add_argument("--telegram-chat-id", help="텔레그램 채팅 ID")
    return parser.parse_args(argv)


def apply_cli_overrides(args: argparse.Namespace) -> None:
    arg_to_env = {
        "start_hotkey": "START_HOTKEY",
        "stop_hotkey": "STOP_HOTKEY",
        "image_match_confidence": "IMAGE_MATCH_CONFIDENCE",
        "enable_waiting_list": "ENABLE_WAITING_LIST",
        "roi_enabled": "ROI_ENABLED",
        "reservation_scan_timeout_sec": "RESERVATION_SCAN_TIMEOUT_SEC",
        "refresh_settle_delay_sec": "REFRESH_SETTLE_DELAY_SEC",
        "enable_telegram_notification": "ENABLE_TELEGRAM_NOTIFICATION",
        "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
        "telegram_chat_id": "TELEGRAM_CHAT_ID",
    }
    for field, env_key in arg_to_env.items():
        value = getattr(args, field, None)
        if value is None:
            continue
        if isinstance(value, bool):
            os.environ[env_key] = "true" if value else "false"
        else:
            os.environ[env_key] = str(value)


if __name__ == "__main__":
    dotenv.load_dotenv()

    cli_args = parse_cli_args()
    apply_cli_overrides(cli_args)

    srt_config = load_config_from_env()
    macro_agent = SRTMacroAgent(srt_config)
    macro_agent.run()
