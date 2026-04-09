import unicodedata
from pathlib import Path

from srt_macro_reservation.models import TemplateSet


class TemplateStore:
    def __init__(self, target_dir: Path):
        self._target_dir = target_dir

    def load(self) -> TemplateSet:
        return TemplateSet(
            booking=self._resolve_booking_candidates("예약하기"),
            waiting=self._resolve(("예약대기", "신청하기")),
            refresh=self._resolve(("조회하기",)),
            sold_out=self._resolve(("매진",)),
            connection_wait=self._resolve(("접속대기",)),
        )

    def _resolve(self, names: tuple[str, ...]) -> Path | None:
        if not self._target_dir.exists():
            return None

        normalized_targets = {self._normalize_text(name) for name in names}
        for image_path in sorted(self._target_dir.glob("*.png")):
            image_stem = self._normalize_text(image_path.stem)
            if image_stem in normalized_targets:
                return image_path
        return None

    def _resolve_booking_candidates(self, name: str) -> tuple[Path, ...]:
        if not self._target_dir.exists():
            return ()

        normalized_name = self._normalize_text(name)
        prefixed_name = f"{normalized_name}_"
        exact_matches: list[Path] = []
        prefixed_matches: list[Path] = []

        image_paths = sorted(
            self._target_dir.glob("*.png"),
            key=lambda path: self._normalize_text(path.name),
        )
        for image_path in image_paths:
            image_stem = self._normalize_text(image_path.stem)
            if image_stem == normalized_name:
                exact_matches.append(image_path)
                continue
            if image_stem.startswith(prefixed_name):
                prefixed_matches.append(image_path)

        return tuple(exact_matches + prefixed_matches)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return unicodedata.normalize("NFC", value.strip())
