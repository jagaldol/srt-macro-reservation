import asyncio
import time
from typing import Optional

from telegram import Bot, Update


class SRTMacroBot:
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self._last_update_id: Optional[int] = None
        self._stop_requested = False
        self._loop: asyncio.AbstractEventLoop | None = asyncio.new_event_loop()

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
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.alert(text=text, duration=duration))

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
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop
