# 🚄 srt-macro-reservation

SRT 잔여 좌석(취소표)을 자동으로 탐색하고, 좌석이 발견되면 즉시 예약을 시도하며, Telegram 알림을 통해 실시간으로 사용자에게 결과를 알려주는 자동화 매크로 도구입니다.

## ✅ 주요 기능

- 특정 시간 이후의 SRT 노선(예: 수서 → 부산) 잔여 좌석 자동 조회
- 2시간 단위로 묶여 제공되는 조회 결과에서 `NUM_TO_SKIP`과 `NUM_TO_CHECK`로 원하는 열차 시간대를 세밀하게 타겟팅
- 잔여 좌석이 발견되면 즉시 **자동 예약** 또는 **예약 대기 신청**, 필요 시 예약 대기 기능은 `ENABLE_WAITING_LIST`로 끌 수 있음
- 성공 여부를 **Telegram 알림**으로 실시간 전송하고, 실행 직후에는 선택한 설정 요약 메시지를 전송
- 텔레그램 알림은 `/stop` 명령으로 조기 중지할 수 있으며, 예약 성공 시 기본 5분간 5초 간격으로 반복 알림
- 예약 성공 시 자동 종료 또는 반복 실행 가능

## 🧰 사용 기술

- Python 3.10+
- Selenium (Chrome WebDriver 기반 브라우저 자동화)
- Telegram Bot API
- Windows CMD 환경 실행 지원 (`.bat` 파일 포함)

## 📦 설치 및 실행 방법

### 1. 레포지토리 클론 및 의존성 설치

```bash
git clone https://github.com/yourname/srt-macro-reservation.git
cd srt-macro-reservation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 환경 설정 (.env 파일 작성)

프로젝트 루트에 `.env.example`을 `.env`로 복사하여 다음 항목을 채워주세요:

```
DEPARTURE_STATION=수서
ARRIVAL_STATION=부산
DEPARTURE_DATE=20250101           # 출발일 (YYYYMMDD)
DEPARTURE_TIME=10                 # 출발 시간 (00~22 | 2시간 단위(짝수))
NUM_TO_CHECK=3                    # 조회할 열차 개수
NUM_TO_SKIP=0                     # 앞에서 건너뛸 열차 개수
USER_ID=1234567890                # SRT 로그인 ID
PASSWORD=0000                     # SRT 비밀번호
ENABLE_WAITING_LIST=true          # 예약 대기 자동 시도 여부 (true/false)
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TELEGRAM_CHAT_ID=1234567890
```

> telegram bot father를 통해 봇을 만들고 해당 봇의 토큰과 봇과의 채팅방 id를 넣어야합니다.

### 환경 변수 상세 설명

| 변수 | 설명 | 예시 | 필수 | 기본값 |
| --- | --- | --- | --- | --- |
| `DEPARTURE_STATION` | 출발역 | `수서` | ✅ | - |
| `ARRIVAL_STATION` | 도착역 | `부산` | ✅ | - |
| `DEPARTURE_DATE` | 출발 날짜 (YYYYMMDD) | `20250101` | ✅ | - |
| `DEPARTURE_TIME` | 조회 시작 시간 (짝수, HH) | `10` | ✅ | - |
| `NUM_TO_CHECK` | 각 새로고침마다 확인할 열차 수 | `3` | ✅ | `3` |
| `NUM_TO_SKIP` | 결과 상단에서 건너뛸 열차 수 | `0` | ✅ | `0` |
| `USER_ID` | SRT 로그인 ID | `1234567890` | ✅ | - |
| `PASSWORD` | SRT 비밀번호 | `0000` | ✅ | - |
| `ENABLE_WAITING_LIST` | 자동 예약대기 신청 여부 (`true`/`false`) | `true` | ✅ | `true` |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 (미입력 시 알림 비활성화) | `123456...` | 선택 | - |
| `TELEGRAM_CHAT_ID` | 알림을 받을 채팅방 ID (미입력 시 알림 비활성화) | `1234567890` | 선택 | - |

> 텔레그램 토큰/채팅 ID를 비워두면 알림이 비활성화된 상태로 실행됩니다.

#### Telegram 채팅방 ID 빠르게 확인하기

텔레그램 채팅방 ID를 알고 싶다면 다음 명령으로 제공된 도우미 스크립트를 실행하세요.

```bash
python find_bot_chat_id.py
```

봇과 대화를 시작한 뒤 `/chatId` 명령을 보내면 채팅방 ID를 회신합니다.

## 3. 실행 방법

▶ Windows에서 .bat로 실행

```cmd
run.bat
```

▶ 직접 실행

```
.venv\Scripts\activate
python main.py
```

## ℹ️ SRT 예약과 예약대기의 차이점

SRT는 두 가지 방식으로 좌석을 확보할 수 있습니다:

- **예약**: 잔여 좌석이 있는 경우 즉시 좌석 확보가 가능하며, **15분 이내에 결제**를 완료해야만 최종 예약이 완료됩니다.  
  ⮕ 따라서 **즉시 알림과 빠른 사용자 응답**이 매우 중요합니다.

- **예약 대기**: 현재 좌석이 없더라도 대기열에 등록하는 방식으로, 좌석이 취소될 경우 자동으로 배정됩니다. 이 경우 **충분한 시간 내에 결제**가 가능하며, 긴급하지는 않습니다.

이 도구는 두 방식 모두를 자동으로 처리하며, 아래와 같이 알림 강도를 다르게 설정합니다:

- **예약 성공** 시 → **5초 간격으로 5분간 반복 알림** 전송하여 사용자가 즉시 결제하도록 유도합니다.
- **예약 대기 성공** 시 → **1회 알림**만 전송합니다.

## 💬 텔레그램 알림 예시

- **예약 성공**: "예약에 성공하였습니다."  
  → 5초 간격으로 5분간 반복 알림 전송
- **예약 대기 성공**: "예약 대기에 성공하였습니다."

텔레그램 알림 중에는 `/stop` 명령으로 즉시 알림을 종료하고 프로그램을 마무리할 수 있습니다. 실행이 시작되면 설정 요약이 한 번 전송되어 현재 탐색 중인 노선을 확인할 수 있습니다.
