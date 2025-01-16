import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello {update.effective_user.first_name}")


async def chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id  # 여기에서 채팅방 ID 확인 가능

    # 채팅방 ID를 메시지로 보내기
    await context.bot.send_message(chat_id=chat_id, text=f"이 채팅방의 ID는: {chat_id} 입니다.")


if __name__ == "__main__":
    load_dotenv()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("chatId", chat_id))

    app.run_polling()
