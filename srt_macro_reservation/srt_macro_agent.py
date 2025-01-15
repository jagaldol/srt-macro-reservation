import time
from random import randint

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from srt_macro_reservation.config import SRTConfig


class SRTMacroAgent:
    def __init__(self, config: SRTConfig, driver: WebDriver):
        self.config = config
        self.driver = driver
        self.is_booked = False
        self.refresh_count = 0

    def run(self):
        while not self.is_booked:
            for train_index in range(1, self.config.num_to_check + 1):
                try:
                    standard_seat_status = self.driver.find_element(
                        By.CSS_SELECTOR,
                        f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({train_index}) > td:nth-child(7)",
                    ).text
                    reservation_status = self.driver.find_element(
                        By.CSS_SELECTOR,
                        f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({train_index}) > td:nth-child(8)",
                    ).text
                except StaleElementReferenceException:
                    standard_seat_status = "매진"
                    reservation_status = "매진"

                self.attempt_booking(standard_seat_status, train_index)
                self.attempt_reservation(reservation_status, train_index)

            time.sleep(randint(2, 4))
            self.refresh_results()

    def attempt_booking(self, seat_status, train_index):
        if "예약하기" in seat_status:
            print("\nAttempting to book a seat...")
            try:
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({train_index}) > td:nth-child(7) > a",
                ).click()
            except ElementClickInterceptedException as e:
                print(f"\nError clicking the booking button: {e}")
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({train_index}) > td:nth-child(7) > a",
                ).send_keys(Keys.ENTER)

            self.driver.implicitly_wait(3)

            if self.driver.find_elements(By.ID, "isFalseGotoMain"):
                self.is_booked = True
                print("\nBooking successful!")
            else:
                print("\nNo available seats. Returning to results page.")
                self.driver.back()
                self.driver.implicitly_wait(5)

    def attempt_reservation(self, reservation_status, train_index):
        if "신청하기" in reservation_status:
            print("\nAttempting to place a reservation...")
            self.driver.find_element(
                By.CSS_SELECTOR,
                f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({train_index}) > td:nth-child(8) > a",
            ).click()
            self.is_booked = True

    def refresh_results(self):
        refresh_button = self.driver.find_element(By.XPATH, "//input[@value='조회하기']")
        self.driver.execute_script("arguments[0].click();", refresh_button)
        self.refresh_count += 1
        print(f"\rRefreshed results {self.refresh_count} times.", end="")
        self.driver.implicitly_wait(10)
        time.sleep(0.5)
