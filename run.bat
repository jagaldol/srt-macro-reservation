@chcp 65001 >nul
@echo off
REM 가상 환경 활성화
call .venv\Scripts\activate

REM main.py 실행
python main.py

REM 스크립트 종료 시 메시지 표시
echo 실행이 완료되었습니다. 창을 닫으려면 아무 키나 누르세요...
pause