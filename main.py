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
    else:
        print("Telegram 알림을 비활성화했습니다. 토큰과 채팅 ID를 확인하세요.")

    macro_agent = SRTMacroAgent(srt_config, driver, bot=srt_macro_bot)
    macro_agent.run()
