import asyncio
import os

import dotenv

from srt_macro_reservation.config import load_config_from_env
from srt_macro_reservation.srt_chrome_driver_loader import SRTChromeDriverLoader
from srt_macro_reservation.srt_macro_agent import SRTMacroAgent
from telegram_notification.srt_macro_bot import SRTMacroBot

if __name__ == "__main__":
    dotenv.load_dotenv()

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
        asyncio.run(srt_macro_bot.alert(text=config_summary, duration=0))
    else:
        print("Telegram 알림을 비활성화했습니다. 토큰과 채팅 ID를 확인하세요.")

    macro_agent = SRTMacroAgent(srt_config, driver, bot=srt_macro_bot)
    macro_agent.run()
