import time
from random import randint

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    JavascriptException,
    NoAlertPresentException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from srt_macro_reservation.config import SRTConfig
from telegram_notification.srt_macro_bot import SRTMacroBot


class SRTMacroAgent:
    def __init__(
        self,
        config: SRTConfig,
        driver: WebDriver,
        bot: SRTMacroBot,
        wait_timeout: int = 10,
    ):
        self.config = config
        self.driver = driver
        self.bot = bot
        self.refresh_count = 0
        self.wait_timeout = wait_timeout

    def run(self):
        self._wait_for_results_table()
        if not self.config.enable_waiting_list:
            print("\n예약대기 자동 신청을 비활성화했습니다.")
        start_index = 1 + self.config.num_to_skip
        end_index = start_index + self.config.num_to_check
        while True:
            for train_index in range(start_index, end_index):
                standard_seat_status = self._get_cell_text(train_index, 7)
                reservation_status = self._get_cell_text(train_index, 8)

                if self.attempt_booking(standard_seat_status, train_index):
                    self._notify_success("booking")
                    return
                if self.attempt_reservation(reservation_status, train_index):
                    self._notify_success(
                        "waitlist",
                        text="예약대기에 성공하였습니다",
                        duration=0,
                    )
                    return

            time.sleep(randint(2, 4))
            self.refresh_results()

    def attempt_booking(self, seat_status, train_index):
        if "예약하기" not in seat_status:
            return False

        print("\nAttempting to book a seat... " f"(after {self.refresh_count} refreshes)")
        button_locator = (
            By.CSS_SELECTOR,
            (
                "#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > "
                f"tr:nth-child({train_index}) > td:nth-child(7) > a"
            ),
        )
        current_handles = set(self.driver.window_handles)

        if not self._click_element(button_locator, "booking button"):
            return False

        alert_text = self._handle_alert()

        if alert_text:
            print(f"\n예약 진행 중 경고창이 표시되었습니다: {alert_text}")
            self._wait_for_results_table()
            return False

        if self._switch_to_booking_window(current_handles):
            print("\nBooking page detected. Awaiting user action.")
            return True

        if self._is_on_booking_page():
            print("\nBooking page detected. Awaiting user action.")
            return True

        print("\nNo available seats. Returning to results page.")
        self.driver.back()
        self._wait_for_results_table()
        return False

    def attempt_reservation(self, reservation_status, train_index):
        if not self.config.enable_waiting_list:
            return False
        if "신청하기" not in reservation_status:
            return False

        print("\nAttempting to place a reservation... " f"(after {self.refresh_count} refreshes)")
        reservation_locator = (
            By.CSS_SELECTOR,
            (
                "#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > "
                f"tr:nth-child({train_index}) > td:nth-child(8) > a"
            ),
        )
        return self._click_element(reservation_locator, "reservation button")

    def refresh_results(self):
        refresh_locator = (By.XPATH, "//input[@value='조회하기']")
        if self._click_element(refresh_locator, "refresh button"):
            self.refresh_count += 1
            print(f"\rRefreshed results {self.refresh_count} times.", end="")
            self._wait_for_results_table()

    def _get_cell_text(self, train_index: int, column_index: int) -> str:
        selector = (
            "#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > "
            f"tr:nth-child({train_index}) > td:nth-child({column_index})"
        )
        for _ in range(2):
            try:
                return self.driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            except (NoSuchElementException, StaleElementReferenceException):
                time.sleep(0.2)
                self._wait_for_results_table()
        return ""

    def _notify_success(
        self,
        success_type: str,
        text: str | None = None,
        duration: int = 300,
    ):
        refresh_message = f"{self.refresh_count}번 새로고침 후 " if self.refresh_count else "첫 조회에서 "

        if success_type == "booking":
            base_message = "Booking successful!"
            default_text = "예약에 성공하였습니다."
            detail_message = f"{refresh_message}예약 버튼을 통해 좌석을 확보했습니다."
        else:
            base_message = "Reservation successful!"
            default_text = "예약대기에 성공하였습니다."
            detail_message = f"{refresh_message}예약대기 신청이 완료되었습니다."

        print(f"\n{base_message}")
        print(detail_message)

        if not self.bot:
            return
        message_text = text or default_text
        message_text = f"{message_text}\n{detail_message}"
        self.bot.alert_sync(text=message_text, duration=duration)

    def _handle_alert(self) -> str | None:
        try:
            alert = self.driver.switch_to.alert
        except NoAlertPresentException:
            return None

        print(f"\nAlert appeared: {alert.text}")
        alert.accept()
        print("\nAlert accepted.")
        return alert.text

    def _wait_for_results_table(self):
        results_locator = (
            By.CSS_SELECTOR,
            "#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr",
        )
        try:
            WebDriverWait(self.driver, self.wait_timeout).until(EC.presence_of_element_located(results_locator))
        except TimeoutException:
            pass

    def _switch_to_booking_window(self, previous_handles: set[str]) -> bool:
        try:
            WebDriverWait(self.driver, self.wait_timeout).until(
                lambda driver: len(driver.window_handles) > len(previous_handles)
            )
        except TimeoutException:
            return False

        new_handles = [handle for handle in self.driver.window_handles if handle not in previous_handles]
        if not new_handles:
            return False

        self.driver.switch_to.window(new_handles[0])
        return True

    def _is_on_booking_page(self) -> bool:
        keywords = ["승차권 예약", "예약 정보", "결제", "탑승객"]
        page_source = self.driver.page_source
        return any(keyword in page_source for keyword in keywords)

    def _click_element(self, locator: tuple[str, str], description: str) -> bool:
        last_error: Exception | None = None
        for _ in range(2):
            try:
                element = WebDriverWait(self.driver, self.wait_timeout).until(EC.element_to_be_clickable(locator))
                element.click()
                return True
            except (ElementClickInterceptedException, ElementNotInteractableException) as error:
                last_error = error
                try:
                    element = self.driver.find_element(*locator)
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        element,
                    )
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except (JavascriptException, StaleElementReferenceException) as fallback_error:
                    last_error = fallback_error
            except (TimeoutException, StaleElementReferenceException) as error:
                last_error = error
                time.sleep(0.2)

        if last_error:
            print(f"\nFailed to click {description}: {last_error}")
        return False
