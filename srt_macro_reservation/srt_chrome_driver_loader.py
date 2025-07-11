import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from srt_macro_reservation.config import SRTConfig


class SRTChromeDriverLoader:
    def __init__(self, config: SRTConfig):
        self.config = config

        self.driver = webdriver.Chrome()

    def get_search_page_driever(self):
        self._login()
        self._search_trains()
        return self.driver

    def _login(self):
        self.driver.get("https://etk.srail.co.kr/cmc/01/selectLoginForm.do")
        self.driver.implicitly_wait(15)

        self.driver.find_element(By.ID, "srchDvNm01").send_keys(self.config.user_id)
        self.driver.find_element(By.ID, "hmpgPwdCphd01").send_keys(self.config.password)
        self.driver.find_element(By.CSS_SELECTOR, "input.loginSubmit").click()
        time.sleep(2)
        self.driver.implicitly_wait(5)

    def _search_trains(self):
        self.driver.get("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do")
        self.driver.implicitly_wait(5)

        # Enter departure station
        departure_field = self.driver.find_element(By.ID, "dptRsStnCdNm")
        departure_field.clear()
        departure_field.send_keys(self.config.departure_station)

        # Enter arrival station
        arrival_field = self.driver.find_element(By.ID, "arvRsStnCdNm")
        arrival_field.clear()
        arrival_field.send_keys(self.config.arrival_station)

        # Enter departure date
        departure_date_field = self.driver.find_element(By.ID, "dptDt")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", departure_date_field)
        print(self.config.departure_date)
        Select(departure_date_field).select_by_value(self.config.departure_date)

        # Enter departure time
        departure_time_field = self.driver.find_element(By.ID, "dptTm")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", departure_time_field)
        Select(departure_time_field).select_by_visible_text(self.config.departure_time)

        print(
            "Searching for trains:\n"
            f"Departure: {self.config.departure_station}\n"
            f"Arrival: {self.config.arrival_station}\n"
            f"Date: {self.config.departure_date}\n"
            f"Time: {self.config.departure_time} onwards\n"
            f"Checking top {self.config.num_to_check} trains for reservations."
        )

        self.driver.find_element(By.XPATH, "//input[@value='조회하기']").click()
        self.driver.implicitly_wait(5)
        time.sleep(1)
