@echo off
call .venv\Scripts\activate

python main.py ^
  --start-hotkey "f9" ^
  --stop-hotkey "esc" ^
  --image-match-confidence 0.70 ^
  --enable-waiting-list true ^
  --roi-enabled true ^
  --reservation-scan-timeout-sec 5 ^
  --refresh-settle-delay-sec 0.18 ^
  --enable-telegram-notification true ^
  --telegram-bot-token "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ" ^
  --telegram-chat-id "1234567890"

echo Run finished. Press any key to close this window...
pause
