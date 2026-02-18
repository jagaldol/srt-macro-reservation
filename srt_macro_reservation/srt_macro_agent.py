import json
import platform
import threading
import time
from pathlib import Path

from pynput import keyboard

from srt_macro_reservation.config import SRTConfig
from srt_macro_reservation.models import RefreshOutcome, ScanPhase
from srt_macro_reservation.notifier import ReservationNotifier
from srt_macro_reservation.screen_controller import ScreenController
from srt_macro_reservation.template_store import TemplateStore


class SRTMacroAgent:
    def __init__(self, config: SRTConfig):
        self.config = config
        self.refresh_count = 0

        self._base_dir = Path(__file__).resolve().parents[1]
        self._target_dir = self._base_dir / "targets"
        self._runtime_dir = self._base_dir / "runtime"
        self._runtime_dir.mkdir(exist_ok=True)

        self._result_region = self._load_result_region()
        self._templates = TemplateStore(self._target_dir).load()
        self._screen = ScreenController(base_confidence=self.config.image_match_confidence)
        self._notifier = ReservationNotifier(
            enable_telegram=self.config.enable_telegram_notification,
            telegram_bot_token=self.config.telegram_bot_token,
            telegram_chat_id=self.config.telegram_chat_id,
        )

        self._running_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._phase = ScanPhase.REFRESH
        self._listener: keyboard.Listener | None = None
        self._last_key_press_at: dict[str, float] = {}

        self._reservation_wait_deadline: float | None = None
        self._last_refresh_wait_log_at = 0.0
        self._last_reservation_wait_log_at = 0.0
        self._last_connection_wait_log_at = 0.0

    def run(self):
        print("\nSRT 이미지 매크로 대기 중입니다.")
        print(f"- 시작 단축키: {self.config.start_hotkey}")
        print(f"- 중지 단축키: {self.config.stop_hotkey}")
        print("- 종료: 터미널에서 Ctrl+C")
        self._print_permission_guide()
        self._print_target_status()

        if not self._templates.refresh:
            print("\n조회하기 템플릿이 없어 매크로를 시작할 수 없습니다. targets/조회하기.png를 추가하세요.")
            return

        worker = threading.Thread(target=self._macro_loop, name="SRTMacroWorker", daemon=True)
        worker.start()

        try:
            self._listener = keyboard.Listener(on_press=self._on_key_press)
            self._listener.start()
        except Exception as error:
            print(f"\n전역 단축키 리스너를 시작할 수 없습니다: {error}")
            print("macOS에서 Python/터미널 앱을 손쉬운 사용 및 입력 모니터링에 추가한 뒤 다시 실행하세요.")
            self._shutdown_event.set()
            self._running_event.clear()
            worker.join(timeout=2)
            return

        try:
            while True:
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
        finally:
            self._shutdown_event.set()
            self._running_event.clear()
            if self._listener:
                self._listener.stop()
            worker.join(timeout=2)

    def _on_key_press(self, key):
        key_name = self._key_to_name(key)
        if not key_name:
            return
        if self._is_debounced(key_name):
            return

        if key_name == self.config.start_hotkey:
            self._reset_cycle_state()
            self._running_event.set()
            print("\n매크로를 시작합니다.")
            return

        if key_name == self.config.stop_hotkey:
            self._running_event.clear()
            print("\n매크로를 중지했습니다.")

    def _macro_loop(self):
        while not self._shutdown_event.is_set():
            if not self._running_event.wait(timeout=0.2):
                continue
            if self._shutdown_event.is_set():
                return

            try:
                if self._phase == ScanPhase.REFRESH:
                    refresh_outcome = self._refresh_results()
                    if refresh_outcome == RefreshOutcome.READY:
                        self._start_reservation_phase()
                    elif refresh_outcome == RefreshOutcome.WAIT_CONNECTION:
                        self._phase = ScanPhase.WAIT_CONNECTION
                        self._last_connection_wait_log_at = 0.0
                    else:
                        self._interruptible_sleep(0.15)
                    continue

                if self._phase == ScanPhase.WAIT_CONNECTION:
                    if self._is_connection_wait_detected():
                        self._log_connection_waiting()
                        self._interruptible_sleep(0.15)
                        continue

                    print("\n접속대기 화면이 사라졌습니다. 예약 단계로 이동합니다.")
                    self._start_reservation_phase()
                    continue

                if self._attempt_booking():
                    self._on_reservation_success("booking")
                    continue

                if self._attempt_waiting_list():
                    self._on_reservation_success("waitlist")
                    continue

                if self._is_connection_wait_detected():
                    print("\n접속대기 화면을 감지했습니다. 접속대기 해제까지 대기합니다.")
                    self._phase = ScanPhase.WAIT_CONNECTION
                    self._last_connection_wait_log_at = 0.0
                    self._interruptible_sleep(0.1)
                    continue

                if self._is_sold_out_detected():
                    print("\n매진 상태를 감지했습니다. 조회하기 단계로 이동합니다.")
                    self._phase = ScanPhase.REFRESH
                    self._reservation_wait_deadline = None
                    continue

                if self._reservation_wait_deadline is not None and time.time() >= self._reservation_wait_deadline:
                    print(f"\n예약 탐색 {self.config.reservation_scan_timeout_sec:.1f}초가 경과했습니다. 조회하기 단계로 이동합니다.")
                    self._phase = ScanPhase.REFRESH
                    self._reservation_wait_deadline = None
                    continue

                self._log_reservation_waiting()
                self._interruptible_sleep(0.05)
            except Exception as error:
                print(f"\n매크로 루프 예외가 발생했습니다: {error}")
                print("매크로를 자동 중지했습니다. 화면/권한/이미지 설정을 확인 후 다시 시작하세요.")
                self._running_event.clear()
                self._reset_cycle_state()

    def _on_reservation_success(self, success_type: str):
        self._running_event.clear()
        self._phase = ScanPhase.REFRESH
        self._reservation_wait_deadline = None
        self._notifier.notify_success(success_type)

    def _start_reservation_phase(self):
        self._phase = ScanPhase.RESERVATION
        self._reservation_wait_deadline = time.time() + self.config.reservation_scan_timeout_sec
        self._last_reservation_wait_log_at = 0.0

    def _reset_cycle_state(self):
        self._phase = ScanPhase.REFRESH
        self._reservation_wait_deadline = None
        self._last_refresh_wait_log_at = 0.0
        self._last_reservation_wait_log_at = 0.0
        self._last_connection_wait_log_at = 0.0

    def _refresh_results(self) -> RefreshOutcome:
        if not self._templates.refresh:
            print("\n조회하기 템플릿이 없어 매크로를 계속할 수 없습니다.")
            return RefreshOutcome.NOT_FOUND

        self._screen.scroll_to_top()
        refresh_region = self._screen.top_search_region()

        if self._screen.locate_and_click(
            image_path=self._templates.refresh,
            description="조회하기",
            region=refresh_region,
            retries=3,
            confidence=self._confidence_for("조회하기"),
        ):
            return self._handle_refresh_click_success("조회 버튼")

        if self._screen.locate_and_click(
            image_path=self._templates.refresh,
            description="조회하기",
            region=None,
            retries=2,
            confidence=self._confidence_for("조회하기"),
        ):
            return self._handle_refresh_click_success("조회 버튼(전체 화면)")

        self._log_refresh_waiting()
        return RefreshOutcome.NOT_FOUND

    def _handle_refresh_click_success(self, source_label: str) -> RefreshOutcome:
        self.refresh_count += 1
        print(f"\r{source_label}으로 새로고침 {self.refresh_count}회", end="")
        time.sleep(self.config.refresh_settle_delay_sec)

        if self._is_connection_wait_detected():
            print("\n접속대기 화면 감지. 접속대기 해제까지 대기합니다.")
            return RefreshOutcome.WAIT_CONNECTION
        return RefreshOutcome.READY

    def _attempt_booking(self) -> bool:
        if not self._templates.booking:
            return False
        return self._screen.locate_and_click(
            image_path=self._templates.booking,
            description="예약하기",
            region=self._result_region,
            retries=1,
            confidence=self._confidence_for("예약하기"),
            move_duration=0.01,
        )

    def _attempt_waiting_list(self) -> bool:
        if not self.config.enable_waiting_list:
            return False
        if not self._templates.waiting:
            return False
        return self._screen.locate_and_click(
            image_path=self._templates.waiting,
            description="예약대기",
            region=self._result_region,
            retries=1,
            confidence=self._confidence_for("예약대기"),
            move_duration=0.01,
        )

    def _is_sold_out_detected(self) -> bool:
        if not self._templates.sold_out:
            return False
        return (
            self._screen.locate_image(
                image_path=self._templates.sold_out,
                region=None,
                retries=1,
                confidence=self._confidence_for("매진"),
            )
            is not None
        )

    def _is_connection_wait_detected(self) -> bool:
        if not self._templates.connection_wait:
            return False
        return (
            self._screen.locate_image(
                image_path=self._templates.connection_wait,
                region=None,
                retries=2,
                confidence=self._confidence_for("접속대기"),
            )
            is not None
        )

    def _confidence_for(self, template_type: str) -> float:
        base = self.config.image_match_confidence
        if template_type == "조회하기":
            return base
        if template_type == "예약하기":
            return max(base, 0.92)
        if template_type == "예약대기":
            return max(base, 0.90)
        if template_type in {"매진", "접속대기"}:
            return max(base, 0.80)
        return base

    def _log_refresh_waiting(self):
        now = time.time()
        if now - self._last_refresh_wait_log_at < 2.0:
            return
        self._last_refresh_wait_log_at = now
        print("\n조회하기 버튼 탐지 대기 중...")

    def _log_reservation_waiting(self):
        now = time.time()
        if now - self._last_reservation_wait_log_at < 1.0:
            return
        self._last_reservation_wait_log_at = now
        print("\n예약/매진 상태 확인 중...")

    def _log_connection_waiting(self):
        now = time.time()
        if now - self._last_connection_wait_log_at < 1.0:
            return
        self._last_connection_wait_log_at = now
        print("\n접속대기 화면 유지 중...")

    def _interruptible_sleep(self, duration: float):
        end_at = time.time() + duration
        while time.time() < end_at:
            if self._shutdown_event.is_set() or not self._running_event.is_set():
                return
            remaining = end_at - time.time()
            if remaining <= 0:
                return
            time.sleep(min(0.05, remaining))

    def _is_debounced(self, key_name: str, cooldown: float = 0.25) -> bool:
        now = time.time()
        last_pressed_at = self._last_key_press_at.get(key_name, 0.0)
        self._last_key_press_at[key_name] = now
        return (now - last_pressed_at) < cooldown

    @staticmethod
    def _key_to_name(key) -> str | None:
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.lower()
        if isinstance(key, keyboard.Key):
            return key.name.lower()
        return None

    def _load_result_region(self) -> tuple[int, int, int, int] | None:
        if not self.config.roi_enabled:
            return None

        region_file = self._runtime_dir / "result_region.json"
        if not region_file.exists():
            return None

        try:
            data = json.loads(region_file.read_text(encoding="utf-8"))
            left = int(data["x"])
            top = int(data["y"])
            width = int(data["width"])
            height = int(data["height"])
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            print(f"\nROI 설정 파일 파싱 실패: {error}")
            return None

        if width <= 0 or height <= 0:
            print("\nROI 설정 파일의 width/height 값이 잘못되었습니다.")
            return None

        return (left, top, width, height)

    def _print_target_status(self):
        if self.config.enable_telegram_notification:
            print("- 알림 방식: 텔레그램")
        else:
            print("- 알림 방식: PC 알림음")

        if self._templates.booking:
            print(f"- 예약하기 템플릿: {self._templates.booking.name}")
        else:
            print("- 예약하기 템플릿: 없음")

        if self.config.enable_waiting_list:
            if self._templates.waiting:
                print(f"- 예약대기 템플릿: {self._templates.waiting.name}")
            else:
                print("- 예약대기 템플릿: 없음 (예약대기는 비활성처럼 동작)")

        if self._templates.refresh:
            print(f"- 조회하기 템플릿: {self._templates.refresh.name}")
        else:
            print("- 조회하기 템플릿: 없음 (필수 파일, 실행 불가)")

        if self._templates.sold_out:
            print(f"- 매진 템플릿: {self._templates.sold_out.name}")
        else:
            print("- 매진 템플릿: 없음 (타임아웃 기준으로 조회 단계 복귀)")

        if self._templates.connection_wait:
            print(f"- 접속대기 템플릿: {self._templates.connection_wait.name}")
        else:
            print("- 접속대기 템플릿: 없음 (조회 후 바로 예약 단계로 진행)")

        if self._result_region:
            left, top, width, height = self._result_region
            print(f"- ROI: x={left}, y={top}, width={width}, height={height}")
        else:
            print("- ROI: 사용 안 함 (전체 화면 탐색)")

    @staticmethod
    def _print_permission_guide():
        if platform.system() != "Darwin":
            return
        print("- macOS 권한 확인: 손쉬운 사용, 입력 모니터링, 화면 기록에서 Python/터미널 앱 허용 필요")
