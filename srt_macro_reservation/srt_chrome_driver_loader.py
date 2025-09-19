import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from srt_macro_reservation.config import SRTConfig


class SRTChromeDriverLoader:
    LOGIN_URL = "https://etk.srail.co.kr/cmc/01/selectLoginForm.do"
    SEARCH_URL = "https://etk.srail.kr/hpg/hra/01/selectScheduleList.do"
    RESULT_ROWS_SELECTOR = (
        "#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr"
    )

    def __init__(self, config: SRTConfig, wait_timeout: int = 10):
        self.config = config
        self.wait_timeout = wait_timeout

        options = Options()
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, self.wait_timeout)

    def get_search_page_driver(self):
        self._login()
        self._search_trains()
        return self.driver

    # NOTE: kept for backward compatibility with existing scripts.
    def get_search_page_driever(self):
        return self.get_search_page_driver()

    def _login(self):
        self.driver.get(self.LOGIN_URL)
        try:
            user_field = self.wait.until(
                EC.visibility_of_element_located((By.ID, "srchDvNm01"))
            )
        except TimeoutException as exc:
            raise RuntimeError("로그인 페이지를 불러오지 못했습니다.") from exc

        user_field.clear()
        user_field.send_keys(self.config.user_id)

        password_field = self.driver.find_element(By.ID, "hmpgPwdCphd01")
        password_field.clear()
        password_field.send_keys(self.config.password)

        login_button = self.driver.find_element(By.CSS_SELECTOR, "input.loginSubmit")
        login_button.click()
        time.sleep(1)

    def _search_trains(self):
        self.driver.get(self.SEARCH_URL)
        try:
            departure_field = self.wait.until(
                EC.element_to_be_clickable((By.ID, "dptRsStnCdNm"))
            )
        except TimeoutException as exc:
            raise RuntimeError("열차 조회 페이지를 불러오지 못했습니다.") from exc

        departure_field.clear()
        departure_field.send_keys(self.config.departure_station)

        arrival_field = self.wait.until(
            EC.element_to_be_clickable((By.ID, "arvRsStnCdNm"))
        )
        arrival_field.clear()
        arrival_field.send_keys(self.config.arrival_station)

        self._select_option("dptDt", value=self.config.departure_date)
        self._select_option("dptTm", text=self.config.departure_time)

        message = (
            "Searching for trains:\n"
            f"Departure: {self.config.departure_station}\n"
            f"Arrival: {self.config.arrival_station}\n"
            f"Date: {self.config.departure_date}\n"
            f"Time: {self.config.departure_time} onwards\n"
            f"Inspecting {self.config.num_to_check} trains for availability."
        )
        if self.config.num_to_skip:
            message += f"\nSkipping first {self.config.num_to_skip} trains."
        print(message)

        search_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='조회하기']"))
        )
        search_button.click()

        try:
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.RESULT_ROWS_SELECTOR))
            )
        except TimeoutException:
            pass
        time.sleep(0.5)

    def _select_option(self, element_id: str, *, value: str | None = None, text: str | None = None):
        try:
            element = self.wait.until(EC.presence_of_element_located((By.ID, element_id)))
        except TimeoutException as exc:
            raise RuntimeError(f"{element_id} 요소를 찾을 수 없습니다.") from exc

        self.driver.execute_script(
            "arguments[0].style.display = 'block';",
            element,
        )

        selector = Select(element)
        if value is not None:
            try:
                selector.select_by_value(value)
                return
            except NoSuchElementException:
                if text is None:
                    raise RuntimeError(f"{element_id}에서 {value} 값을 찾을 수 없습니다.")

        if text is not None:
            try:
                selector.select_by_visible_text(text)
                return
            except NoSuchElementException as exc:
                raise RuntimeError(
                    f"{element_id}에서 {text} 옵션을 찾을 수 없습니다."
                ) from exc

        raise ValueError("value 또는 text 중 하나는 반드시 제공되어야 합니다.")
