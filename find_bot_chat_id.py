import json
import os
import urllib.parse
import urllib.request

import dotenv


def fetch_updates(bot_token: str):
    query = urllib.parse.urlencode({"timeout": 3})
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates?{query}"
    with urllib.request.urlopen(url, timeout=10) as response:
        payload = response.read().decode("utf-8", errors="ignore")
    data = json.loads(payload)
    if not data.get("ok"):
        raise RuntimeError("Telegram API 호출이 실패했습니다.")
    return data.get("result", [])


def extract_chat_infos(updates: list[dict]):
    result: dict[str, str] = {}
    for update in updates:
        message = update.get("message") or update.get("edited_message")
        if not message:
            continue
        chat = message.get("chat") or {}
        chat_id = str(chat.get("id", ""))
        if not chat_id:
            continue
        title = chat.get("title") or chat.get("username") or chat.get("first_name") or "(unknown)"
        result[chat_id] = str(title)
    return result


def main():
    dotenv.load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN 환경변수를 먼저 설정하세요.")
        return

    updates = fetch_updates(bot_token)
    chat_infos = extract_chat_infos(updates)
    if not chat_infos:
        print("수신된 채팅이 없습니다. 텔레그램에서 봇에게 먼저 메시지를 보내세요.")
        return

    print("발견된 chat_id 목록:")
    for chat_id, title in chat_infos.items():
        print(f"- {chat_id} ({title})")


if __name__ == "__main__":
    main()
