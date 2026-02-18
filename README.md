# 🚄 SRT 이미지 매크로 예약 도우미

SRT 웹페이지에서 사용자가 직접 조회 화면까지 준비한 뒤,  
이미지 인식 + 키보드/마우스 제어로 `조회하기` 재조회와 `예약하기/예약대기` 클릭을 자동화하는 프로젝트입니다.

## 📌 프로젝트 개요

이 프로젝트는 다음 상황을 위한 도구입니다.

- 사용자가 직접 로그인/조회 조건 설정은 수행
- 열차 목록 화면에서 반복 새로고침(재조회)과 빠른 클릭만 자동화
- 잔여 좌석이 열리는 짧은 순간에 수동 클릭 지연을 줄이고 싶을 때

즉, 브라우저를 Selenium으로 직접 조작하는 방식이 아니라,  
현재 화면을 이미지로 인식해서 버튼을 찾고 클릭하는 방식입니다.

## ✨ 주요 기능

- `조회하기` 버튼 자동 탐지 및 반복 클릭
- `예약하기`, `예약대기(또는 신청하기)` 버튼 고속 탐지/클릭
- `매진`, `접속대기` 상태 이미지 감지 후 단계 전환
- 전역 단축키로 시작/중지 (`START_HOTKEY`, `STOP_HOTKEY`)
- ROI(관심 영역) 기반 탐지 최적화 지원
- ROI는 `예약하기/예약대기` 탐지에만 적용
- 열차 조회 완료 후 표시되는 열차 목록에서, 예약 버튼이 있는 구간만 핀포인트 탐지 가능
- 원하는 열차 조건/시간대가 표시되는 구간만 집중 탐지하여 오탐을 줄이고 반응 속도를 높임
- 알림 방식 선택
  - 텔레그램 알림
  - PC 알림음
- 텔레그램 설정값이 비어있거나 유효하지 않으면 자동으로 PC 알림음으로 fallback

## 🧭 동작 흐름

1. 사용자가 SRT 사이트에서 직접 조회 조건 입력 후 열차 목록을 띄웁니다.
2. 시작 단축키(기본 `f9`)를 누릅니다.
3. 매크로가 화면 상단으로 스크롤 후 `조회하기`를 클릭합니다.
4. 조회 직후 지정 시간 동안 `예약하기/예약대기`를 빠르게 반복 탐지합니다.
5. 클릭 성공 시 매크로를 중지하고 알림을 보냅니다.

## 🗂 템플릿 이미지 폴더

- `targets/`: 실제 실행에 사용하는 사용자 환경 전용 템플릿 폴더 (git 추적 제외)
- `target_samples/`: 예시 템플릿 샘플 폴더 (git 추적됨)

처음에는 샘플을 복사해서 시작하고, 환경에 맞게 다시 캡처하는 것을 권장합니다.

```bash
cp target_samples/*.png targets/
```

필수/선택 템플릿:

- 필수: `조회하기.png`
- 권장: `예약하기.png`, `예약대기.png`(또는 `신청하기.png`)
- 선택: `매진.png`, `접속대기.png`

## ⚙️ 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 🔧 환경 변수 설정

`.env.example`를 복사해 `.env`를 만든 뒤 값을 설정하세요.

```bash
cp .env.example .env
```

| 변수                           | 설명                              | 기본값      |
| ------------------------------ | --------------------------------- | ----------- |
| `START_HOTKEY`                 | 매크로 시작 단축키                | `f9`        |
| `STOP_HOTKEY`                  | 매크로 중지 단축키                | `esc`       |
| `IMAGE_MATCH_CONFIDENCE`       | 이미지 매칭 기준 confidence       | `0.70`      |
| `ENABLE_WAITING_LIST`          | 예약대기 자동 시도 여부           | `true`      |
| `ROI_ENABLED`                  | ROI 사용 여부                     | `true`      |
| `RESERVATION_SCAN_TIMEOUT_SEC` | 조회 후 예약 탐색 유지 시간(초)   | `5`         |
| `REFRESH_SETTLE_DELAY_SEC`     | 조회 클릭 후 화면 안정화 대기(초) | `0.18`      |
| `ENABLE_TELEGRAM_NOTIFICATION` | 텔레그램 알림 사용 여부           | `false`     |
| `TELEGRAM_BOT_TOKEN`           | 텔레그램 봇 토큰                  | placeholder |
| `TELEGRAM_CHAT_ID`             | 텔레그램 채팅 ID                  | placeholder |

- `ENABLE_TELEGRAM_NOTIFICATION=true`일 때 토큰/chat_id가 비어있거나 예시값이면 텔레그램 전송은 건너뛰고 PC 알림음으로 자동 fallback 됩니다.
- 텔레그램 알림을 실제로 받으려면 토큰/chat_id를 실제 값으로 입력하세요.

## ▶️ 실행

기본 실행:

```bash
./run.sh
```

직접 인자 실행:

```bash
python main.py \
  --start-hotkey "f9" \
  --stop-hotkey "esc" \
  --image-match-confidence 0.70 \
  --enable-waiting-list true \
  --roi-enabled true \
  --reservation-scan-timeout-sec 5 \
  --refresh-settle-delay-sec 0.18 \
  --enable-telegram-notification false
```

Windows:

```bat
run.bat
```

텔레그램 실행(예시 인자 포함):

```bash
./run_telegram.sh
```

```bat
run_telegram.bat
```

참고:

- `run_telegram.*` 스크립트는 `.env.example`의 예시 텔레그램 값을 인자로 사용합니다.
- 예시값 그대로 실행하면 텔레그램 전송 대신 PC 알림음 fallback이 동작합니다.

## 🛠 보조 스크립트

- ROI 저장: `calculate_result_region.py`
- 텔레그램 chat_id 확인: `find_bot_chat_id.py`

## 🚀 고급 활용

### 1. ROI(결과 영역) 캘리브레이션

탐지 속도/정확도를 높이고 싶다면 열차 결과 테이블 영역만 ROI로 지정하세요.

핵심 포인트:

- ROI는 열차 조회 완료 후 화면에 보이는 열차 목록 중 `예약하기/예약대기` 버튼이 나타나는 구간만 탐지 대상으로 제한합니다.
- 즉, 화면 전체를 매번 스캔하지 않고 필요한 영역만 빠르게 확인합니다.
- 같은 조회 페이지에서도 내가 원하는 열차 조건이 노출되는 구간만 정밀하게 타겟팅할 수 있습니다.

```bash
python calculate_result_region.py
```

실행 후 안내에 따라:

1. 결과 영역 왼쪽 위 좌표 선택
2. 결과 영역 오른쪽 아래 좌표 선택

저장 위치:

- `runtime/result_region.json`

적용 조건:

- `.env`에서 `ROI_ENABLED=true`

### 2. 텔레그램 알림 설정

1. BotFather에서 봇 생성 후 토큰 확보
2. 봇과 1회 이상 대화 시작
3. chat_id 조회:

```bash
python find_bot_chat_id.py
```

4. `.env` 설정:

```dotenv
ENABLE_TELEGRAM_NOTIFICATION=true
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TELEGRAM_CHAT_ID=1234567890
```

5. `./run.sh`(또는 `run.bat`) 실행 후 예약/예약대기 클릭 시 알림 수신 확인

참고:

- `ENABLE_TELEGRAM_NOTIFICATION=false`이면 텔레그램 대신 PC 알림음으로 알림합니다.
- `ENABLE_TELEGRAM_NOTIFICATION=true`라도 텔레그램 값이 비어있거나 유효하지 않으면 PC 알림음으로 자동 fallback 됩니다.

## 🧩 트러블슈팅

- `ImageNotFoundException`이 자주 뜨는 경우
  - 템플릿 이미지를 현재 화면 기준으로 다시 캡처
  - 브라우저 배율/해상도 변경 여부 확인
  - `IMAGE_MATCH_CONFIDENCE`를 소폭 낮춰 테스트
- macOS에서 입력 제어가 안 되는 경우
  - 시스템 설정에서 `손쉬운 사용`, `입력 모니터링`, `화면 기록` 권한 허용
- 클릭 좌표가 어긋나는 경우
  - 멀티 모니터/Retina 스케일 환경에서 템플릿 재캡처 후 재시도

## 📚 구버전 문서

기존 Selenium 기반 설명은 `docs/README.selenium-legacy.md`에서 확인할 수 있습니다.

> Selenium 방식은 브라우저 직접 제어로 더 정밀한 조작이 가능하지만,
> SRT 사이트의 자동 제어 방지 강화로 인해 사용 불가하게 되었습니다.

## ⚠️ 주의

- 본 프로젝트는 비공식 자동화 도구입니다.
- 서비스 이용 약관, 관련 정책/법규를 반드시 확인하고 사용하세요.
