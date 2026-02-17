import math
import platform
import time
from pathlib import Path

import pyautogui
import pyscreeze
from pynput import keyboard

from srt_macro_reservation.models import Region


class ScreenController:
    def __init__(self, base_confidence: float):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.03
        self._base_confidence = base_confidence
        self._coord_scale_x, self._coord_scale_y = self._detect_coordinate_scale()
        self._keyboard_controller = self._create_keyboard_controller()

    def locate_and_click(
        self,
        image_path: Path,
        description: str,
        region: Region | None,
        retries: int = 2,
        confidence: float | None = None,
        move_duration: float = 0.08,
    ) -> bool:
        location = self.locate_image(
            image_path=image_path,
            region=region,
            retries=retries,
            confidence=confidence,
        )
        if not location:
            return False

        center = pyautogui.center(location)
        click_x, click_y = self._to_input_coordinates(center.x, center.y)
        pyautogui.moveTo(click_x, click_y, duration=move_duration)
        pyautogui.click()

        current_x, current_y = pyautogui.position()
        if math.hypot(current_x - click_x, current_y - click_y) > 16:
            print("\n마우스 이동이 요청 좌표와 다릅니다. 손쉬운 사용/입력 모니터링 권한을 확인하세요.")
        print(f"\n{description} 클릭(raw=({center.x}, {center.y}), click=({click_x}, {click_y}))")
        return True

    def locate_image(
        self,
        image_path: Path,
        region: Region | None,
        retries: int,
        confidence: float | None = None,
    ):
        search_region = self._to_search_region(region)
        effective_confidence = confidence if confidence is not None else self._base_confidence

        for attempt in range(retries):
            try:
                location = pyautogui.locateOnScreen(
                    str(image_path),
                    region=search_region,
                    confidence=effective_confidence,
                    grayscale=True,
                )
            except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException):
                location = None
            except OSError as error:
                print(f"\n이미지 탐색 중 OS 오류가 발생했습니다: {error}")
                return None

            if location:
                return location
            if attempt + 1 < retries:
                time.sleep(0.12)
        return None

    def scroll_to_top(self):
        for _ in range(3):
            pyautogui.scroll(3000)
            time.sleep(0.05)

        try:
            if platform.system() == "Darwin" and self._keyboard_controller is not None:
                with self._keyboard_controller.pressed(keyboard.Key.cmd):
                    self._keyboard_controller.press(keyboard.Key.up)
                    self._keyboard_controller.release(keyboard.Key.up)
            elif platform.system() != "Darwin":
                pyautogui.press("home")
        except Exception:
            pass

        time.sleep(0.08)

    @staticmethod
    def top_search_region() -> Region:
        screen_width, screen_height = pyautogui.size()
        return (0, 0, screen_width, max(220, int(screen_height * 0.45)))

    def _detect_coordinate_scale(self) -> tuple[float, float]:
        try:
            screen_width, screen_height = pyautogui.size()
            screenshot_width, screenshot_height = pyautogui.screenshot().size
        except Exception:
            return 1.0, 1.0

        if screenshot_width <= 0 or screenshot_height <= 0:
            return 1.0, 1.0

        scale_x = screen_width / screenshot_width
        scale_y = screen_height / screenshot_height
        if abs(scale_x - 1.0) < 0.02 and abs(scale_y - 1.0) < 0.02:
            return 1.0, 1.0

        print(f"- 좌표 보정 스케일 감지: x{scale_x:.3f}, y{scale_y:.3f}")
        return scale_x, scale_y

    @staticmethod
    def _create_keyboard_controller() -> keyboard.Controller | None:
        try:
            return keyboard.Controller()
        except Exception:
            return None

    def _to_input_coordinates(self, x: int, y: int) -> tuple[int, int]:
        screen_width, screen_height = pyautogui.size()
        scaled_x = int(round(x * self._coord_scale_x))
        scaled_y = int(round(y * self._coord_scale_y))
        scaled_x = max(0, min(screen_width - 1, scaled_x))
        scaled_y = max(0, min(screen_height - 1, scaled_y))
        return scaled_x, scaled_y

    def _to_search_region(self, region: Region | None) -> Region | None:
        if region is None:
            return None

        if abs(self._coord_scale_x - 1.0) < 0.02 and abs(self._coord_scale_y - 1.0) < 0.02:
            return region

        left, top, width, height = region
        mapped_left = int(round(left / self._coord_scale_x))
        mapped_top = int(round(top / self._coord_scale_y))
        mapped_width = max(1, int(round(width / self._coord_scale_x)))
        mapped_height = max(1, int(round(height / self._coord_scale_y)))
        return (mapped_left, mapped_top, mapped_width, mapped_height)
