import asyncio
import threading
import time
from typing import Optional

from telegram import Bot, Update


class SRTMacroBot:
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self._last_update_id: Optional[int] = None
        self._stop_requested = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._loop_ready = threading.Event()
        self._loop_lock = threading.Lock()
        self._ensure_loop()

    async def alert(self, text=None, duration=300):
        self._stop_requested = False

        if not text:
            text = "예약에 성공하였습니다."

        await self.bot.send_message(chat_id=self.chat_id, text=text)

        if duration <= 0:
            return

        await self._clear_pending_updates()

        start_time = time.time()
        first_elapsed_sent = False

        while (elapsed_time := time.time() - start_time) < duration:
            await asyncio.sleep(5)
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"경과 시간: {int(elapsed_time)} 초...",
            )
            first_elapsed_sent = True

            await self._check_stop_command()
            if self._stop_requested and first_elapsed_sent:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text="/stop 명령을 수신하여 알림을 중지하고 프로그램을 종료합니다.",
                )
                return

        if not self._stop_requested:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="알림이 최대 동작 시간(5분)을 초과하여 중지되었습니다.",
            )

    def alert_sync(self, text=None, duration=300):
        loop = self._ensure_loop()

        future = asyncio.run_coroutine_threadsafe(
            self.alert(text=text, duration=duration), loop
        )
        try:
            return future.result()
        except RuntimeError as error:
            if "Event loop is closed" in str(error):
                self._restart_loop()
                return self.alert_sync(text=text, duration=duration)
            print(f"Telegram 알림 전송 중 런타임 오류가 발생했습니다: {error}")
        except Exception as error:
            print(f"Telegram 알림 전송 중 오류가 발생했습니다: {error}")

    def _start_loop(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        self._loop_ready.set()
        loop.run_forever()

    def _restart_loop(self):
        with self._loop_lock:
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
            if self._loop_thread and self._loop_thread.is_alive():
                self._loop_thread.join(timeout=1)
            self._loop = None
            self._loop_thread = None
            self._loop_ready.clear()

    async def _check_stop_command(self):
        offset = (self._last_update_id + 1) if self._last_update_id is not None else None
        try:
            updates = await self.bot.get_updates(offset=offset, timeout=1)
        except Exception:
            return

        for update in updates:
            self._last_update_id = update.update_id
            if self._is_stop_command(update):
                self._stop_requested = True

    async def _clear_pending_updates(self):
        try:
            updates = await self.bot.get_updates(timeout=0)
        except Exception:
            return
        if updates:
            self._last_update_id = updates[-1].update_id

    def _is_stop_command(self, update: Update) -> bool:
        message = update.message or update.edited_message
        if not message or not message.text:
            return False
        if str(message.chat_id) != str(self.chat_id):
            return False
        return message.text.strip().lower() == "/stop"

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        with self._loop_lock:
            if self._loop is None or self._loop.is_closed():
                self._loop_ready.clear()
                self._loop = asyncio.new_event_loop()
                self._loop_thread = threading.Thread(
                    target=self._start_loop,
                    name="SRTMacroBotLoop",
                    args=(self._loop,),
                    daemon=True,
                )
                self._loop_thread.start()

        self._loop_ready.wait()
        return self._loop
