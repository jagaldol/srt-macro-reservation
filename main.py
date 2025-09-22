import argparse
import os

import dotenv

from srt_macro_reservation.config import load_config_from_env
from srt_macro_reservation.srt_chrome_driver_loader import SRTChromeDriverLoader
from srt_macro_reservation.srt_macro_agent import SRTMacroAgent
from telegram_notification.srt_macro_bot import SRTMacroBot


def _parse_bool_arg(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "t", "y", "yes"}:
        return True
    if lowered in {"0", "false", "f", "n", "no"}:
        return False
    raise argparse.ArgumentTypeError("true 또는 false 값을 전달해야 합니다.")


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SRT 매크로 실행 설정")
    parser.add_argument("--departure-station", help="SRT 출발역")
    parser.add_argument("--arrival-station", help="SRT 도착역")
    parser.add_argument("--departure-date", help="출발 날짜 (YYYYMMDD)")
    parser.add_argument("--departure-time", help="출발 시간 (짝수, hh 형식)")
    parser.add_argument("--num-to-check", type=int, help="검색 결과 중 시도할 시간표 수")
    parser.add_argument("--num-to-skip", type=int, help="검색 결과에서 건너뛸 시간표 수")
    parser.add_argument("--user-id", help="SRT 사용자 ID")
    parser.add_argument("--password", help="SRT 비밀번호")
    parser.add_argument(
        "--enable-waiting-list",
        type=_parse_bool_arg,
        help="예약대기(신청하기) 자동 시도 여부 (true/false)",
    )
    parser.add_argument("--telegram-bot-token", help="텔레그램 봇 토큰")
    parser.add_argument("--telegram-chat-id", help="텔레그램 채팅 ID")
    return parser.parse_args(argv)


def apply_cli_overrides(args: argparse.Namespace) -> None:
    arg_to_env = {
        "departure_station": "DEPARTURE_STATION",
        "arrival_station": "ARRIVAL_STATION",
        "departure_date": "DEPARTURE_DATE",
        "departure_time": "DEPARTURE_TIME",
        "num_to_check": "NUM_TO_CHECK",
        "num_to_skip": "NUM_TO_SKIP",
        "user_id": "USER_ID",
        "password": "PASSWORD",
        "enable_waiting_list": "ENABLE_WAITING_LIST",
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
    loader = SRTChromeDriverLoader(srt_config)
    driver = loader.get_search_page_driver()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    srt_macro_bot = None
    if bot_token and chat_id:
        srt_macro_bot = SRTMacroBot(bot_token, chat_id)
        config_summary = (
            "SRT 매크로를 다음 설정으로 시작합니다:\n"
            f"- 출발역: {srt_config.departure_station}\n"
            f"- 도착역: {srt_config.arrival_station}\n"
            f"- 출발일시: {srt_config.departure_date} {srt_config.departure_time}시\n"
            f"- 조회 건너뛰기: {srt_config.num_to_skip}건\n"
            f"- 확인 대상: {srt_config.num_to_check}건\n"
            f"- 예약대기 시도: {'예' if srt_config.enable_waiting_list else '아니요'}"
        )
        srt_macro_bot.alert_sync(text=config_summary, duration=0)
    else:
        print("Telegram 알림을 비활성화했습니다. 토큰과 채팅 ID를 확인하세요.")

    macro_agent = SRTMacroAgent(srt_config, driver, bot=srt_macro_bot)
    macro_agent.run()
