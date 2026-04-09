import contextlib
import importlib
import io
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


def _import_agent_module():
    fake_pyautogui = types.ModuleType("pyautogui")
    fake_pyautogui.ImageNotFoundException = type("ImageNotFoundException", (Exception,), {})

    fake_pyscreeze = types.ModuleType("pyscreeze")
    fake_pyscreeze.ImageNotFoundException = type("ImageNotFoundException", (Exception,), {})

    fake_keyboard = types.ModuleType("keyboard")
    fake_keyboard.KeyCode = type("KeyCode", (), {})
    fake_keyboard.Key = type("Key", (), {"cmd": "cmd"})
    fake_keyboard.Controller = type("Controller", (), {})
    fake_keyboard.Listener = type("Listener", (), {})

    fake_pynput = types.ModuleType("pynput")
    fake_pynput.keyboard = fake_keyboard

    with mock.patch.dict(
        sys.modules,
        {
            "pyautogui": fake_pyautogui,
            "pyscreeze": fake_pyscreeze,
            "pynput": fake_pynput,
            "pynput.keyboard": fake_keyboard,
        },
    ):
        sys.modules.pop("srt_macro_reservation.screen_controller", None)
        sys.modules.pop("srt_macro_reservation.srt_macro_agent", None)
        return importlib.import_module("srt_macro_reservation.srt_macro_agent")


class SRTMacroAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent_module = _import_agent_module()
        cls.agent_class = cls.agent_module.SRTMacroAgent

    def test_attempt_booking_checks_templates_in_order_until_match(self):
        agent = object.__new__(self.agent_class)
        agent._templates = SimpleNamespace(
            booking=(Path("예약하기.png"), Path("예약하기_특실.png")),
        )
        agent._screen = mock.Mock()
        agent._screen.locate_and_click.side_effect = (False, True)
        agent._result_region = (10, 20, 30, 40)
        agent._confidence_for = mock.Mock(return_value=0.95)

        result = agent._attempt_booking()

        self.assertTrue(result)
        self.assertEqual(
            agent._screen.locate_and_click.call_args_list,
            [
                mock.call(
                    image_path=Path("예약하기.png"),
                    description="예약하기",
                    region=(10, 20, 30, 40),
                    retries=1,
                    confidence=0.95,
                    move_duration=0.01,
                ),
                mock.call(
                    image_path=Path("예약하기_특실.png"),
                    description="예약하기",
                    region=(10, 20, 30, 40),
                    retries=1,
                    confidence=0.95,
                    move_duration=0.01,
                ),
            ],
        )

    def test_print_target_status_reports_booking_template_count_and_names(self):
        agent = object.__new__(self.agent_class)
        agent.config = SimpleNamespace(
            enable_telegram_notification=False,
            enable_waiting_list=True,
        )
        agent._templates = SimpleNamespace(
            booking=(Path("예약하기.png"), Path("예약하기_특실.png")),
            waiting=Path("예약대기.png"),
            refresh=Path("조회하기.png"),
            sold_out=None,
            connection_wait=None,
        )
        agent._result_region = None

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            agent._print_target_status()

        self.assertIn(
            "- 예약하기 템플릿: 2개 (예약하기.png, 예약하기_특실.png)",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
