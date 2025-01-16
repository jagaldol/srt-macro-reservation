import asyncio
import time

from telegram import Bot


class SRTMacroBot:
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def alert(self, text=None, duration=300):
        if not text:
            text = "예약에 성공하였습니다."
        await self.bot.send_message(chat_id=self.chat_id, text=text)
        # 비동기로 메시지 반복 실행
        if duration <= 0:
            return
        start_time = time.time()  # 시작 시간 기록

        while (elapsed_time := time.time() - start_time) < duration:
            await self.bot.send_message(chat_id=self.chat_id, text=f"경과 시간: {int(elapsed_time)} 초...")
            await asyncio.sleep(5)  # 5초 대기

        await self.bot.send_message(chat_id=self.chat_id, text="알림이 최대 동작 시간(5분)을 초과하여 중지되었습니다.")
