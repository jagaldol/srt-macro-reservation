import tempfile
import unittest
from pathlib import Path

from srt_macro_reservation.template_store import TemplateStore


class TemplateStoreTests(unittest.TestCase):
    def test_booking_prefers_exact_match_then_sorted_prefixed_matches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            for name in ("예약하기_2.png", "예약하기.png", "예약하기_1.png", "예약대기.png"):
                (target_dir / name).touch()

            templates = TemplateStore(target_dir).load()

            self.assertEqual(
                templates.booking,
                (
                    target_dir / "예약하기.png",
                    target_dir / "예약하기_1.png",
                    target_dir / "예약하기_2.png",
                ),
            )
            self.assertEqual(templates.waiting, target_dir / "예약대기.png")

    def test_booking_accepts_prefixed_only_and_ignores_unsupported_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            for name in ("예약하기_특실.png", "예약하기2.png", "예약하기-특실.png", "신청하기.png"):
                (target_dir / name).touch()

            templates = TemplateStore(target_dir).load()

            self.assertEqual(templates.booking, (target_dir / "예약하기_특실.png",))
            self.assertEqual(templates.waiting, target_dir / "신청하기.png")


if __name__ == "__main__":
    unittest.main()
