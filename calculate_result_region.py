import json
from pathlib import Path

import pyautogui


def main():
    print("\n결과 목록(열차 테이블) 영역 ROI를 저장합니다.")
    print("1) 마우스를 결과 영역의 왼쪽 위로 이동한 뒤 Enter")
    input("준비되면 Enter를 누르세요: ")
    top_left = pyautogui.position()
    print(f"왼쪽 위 좌표: {top_left}")

    print("2) 마우스를 결과 영역의 오른쪽 아래로 이동한 뒤 Enter")
    input("준비되면 Enter를 누르세요: ")
    bottom_right = pyautogui.position()
    print(f"오른쪽 아래 좌표: {bottom_right}")

    left = min(top_left.x, bottom_right.x)
    top = min(top_left.y, bottom_right.y)
    width = abs(bottom_right.x - top_left.x)
    height = abs(bottom_right.y - top_left.y)

    if width <= 0 or height <= 0:
        print("유효하지 않은 영역입니다. 다시 시도하세요.")
        return

    data = {
        "x": int(left),
        "y": int(top),
        "width": int(width),
        "height": int(height),
    }

    base_dir = Path(__file__).resolve().parent
    runtime_dir = base_dir / "runtime"
    runtime_dir.mkdir(exist_ok=True)

    output_file = runtime_dir / "result_region.json"
    output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ROI 저장 완료: {output_file}")


if __name__ == "__main__":
    main()
