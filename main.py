import dotenv

from srt_macro_reservation.config import load_config_from_env
from srt_macro_reservation.srt_chrome_driver_loader import SRTChromeDriverLoader
from srt_macro_reservation.srt_macro_agent import SRTMacroAgent

if __name__ == "__main__":
    dotenv.load_dotenv()

    srt_config = load_config_from_env()
    loader = SRTChromeDriverLoader(srt_config)
    driver = loader.get_search_page_driever()
    macro_agent = SRTMacroAgent(srt_config, driver)
    macro_agent.run()
