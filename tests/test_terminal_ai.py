import unittest

from terminal_ai import ChatUI


class CleanAssistantReplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ui = ChatUI()

    def test_removes_assistant_prefix(self) -> None:
        self.assertEqual(
            self.ui._clean_assistant_reply("Assistant: The Series 6 starts at $399."),
            "The Series 6 starts at $399.",
        )

    def test_truncates_when_model_starts_new_speaker(self) -> None:
        reply = (
            "The Series 6 has ECG and SpO2 support.\n"
            "Customer: That sounds good.\n"
            "Assistant: Want more details?"
        )
        self.assertEqual(
            self.ui._clean_assistant_reply(reply),
            "The Series 6 has ECG and SpO2 support.",
        )


if __name__ == "__main__":
    unittest.main()
