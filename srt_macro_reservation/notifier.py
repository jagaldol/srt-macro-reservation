import json
import platform
import subprocess
import threading
import time
from pathlib import Path
from urllib import parse as urllib_parse
from urllib import request as urllib_request


class ReservationNotifier:
    _PLACEHOLDER_BOT_TOKEN = "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    _PLACEHOLDER_CHAT_ID = "1234567890"

    def __init__(
        self,
        enable_telegram: bool,
        telegram_bot_token: str | None,
        telegram_chat_id: str | None,
    ):
        self._enable_telegram = enable_telegram
        self._telegram_bot_token = self._normalize_optional_str(telegram_bot_token)
        self._telegram_chat_id = self._normalize_optional_str(telegram_chat_id)
        self._telegram_failure_reported = False
        self._telegram_ready = self._prepare_telegram()

    def notify_success(self, success_type: str):
        if success_type == "booking":
            message = "예약하기 버튼 클릭을 시도했습니다. 다음 화면을 확인하세요."
        else:
            message = "예약대기 버튼 클릭을 시도했습니다. 다음 화면을 확인하세요."

        print(f"\n{message}")
        if self._telegram_ready:
            self._send_telegram_alert_async(message)
            return
        self._play_local_beep_async()

    def _send_telegram_alert_async(self, text: str):
        if not self._telegram_ready:
            self._play_local_beep_async()
            return

        def _runner():
            try:
                self._send_telegram_alert_sync(text=text)
            except Exception as error:
                self._disable_telegram(f"{error}")
                self._play_local_beep_async()

        threading.Thread(
            target=_runner,
            name="SRTTelegramNotifier",
            daemon=True,
        ).start()

    def _send_telegram_alert_sync(self, text: str):
        payload = urllib_parse.urlencode(
            {
                "chat_id": self._telegram_chat_id,
                "text": text,
            }
        ).encode("utf-8")
        url = f"https://api.telegram.org/bot{self._telegram_bot_token}/sendMessage"
        request = urllib_request.Request(url=url, data=payload, method="POST")

        with urllib_request.urlopen(request, timeout=8) as response:
            body = response.read().decode("utf-8", errors="ignore")
            data = json.loads(body) if body else {}

        if not data.get("ok"):
            raise RuntimeError("Telegram API 응답이 실패로 반환되었습니다.")
        print("\n텔레그램 알림 전송 완료")

    def _prepare_telegram(self) -> bool:
        if not self._enable_telegram:
            return False

        if not self._telegram_bot_token or not self._telegram_chat_id:
            self._disable_telegram("봇 토큰 또는 chat_id 값이 비어 있습니다.")
            return False

        if (
            self._telegram_bot_token == self._PLACEHOLDER_BOT_TOKEN
            or self._telegram_chat_id == self._PLACEHOLDER_CHAT_ID
        ):
            self._disable_telegram("예시(placeholder) 텔레그램 값이 설정되어 있습니다.")
            return False

        return True

    def _disable_telegram(self, reason: str):
        self._telegram_ready = False
        if self._telegram_failure_reported:
            return
        self._telegram_failure_reported = True
        print(f"\n텔레그램 알림 설정에 실패했습니다. ({reason}) 로컬 비프음으로 대체합니다.")

    @staticmethod
    def _normalize_optional_str(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None

    def _play_local_beep_async(self):
        def _runner():
            self._play_local_beep()

        threading.Thread(
            target=_runner,
            name="SRTLocalBeep",
            daemon=True,
        ).start()

    def _play_local_beep(self):
        if platform.system() == "Windows":
            try:
                import winsound  # noqa: PLC0415

                winsound.Beep(1200, 350)
                time.sleep(0.1)
                winsound.Beep(1200, 350)
                return
            except Exception:
                pass

        if platform.system() == "Darwin":
            sound_candidates = (
                "/System/Library/Sounds/Glass.aiff",
                "/System/Library/Sounds/Ping.aiff",
            )
            for sound_path in sound_candidates:
                if not Path(sound_path).exists():
                    continue
                subprocess.run(
                    ["afplay", sound_path],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(0.08)
                subprocess.run(
                    ["afplay", sound_path],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

        print("\a", end="", flush=True)
        time.sleep(0.1)
        print("\a", end="", flush=True)
