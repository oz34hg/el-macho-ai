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


class EnforceIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ui = ChatUI()

    def test_adds_identity_for_self_query(self) -> None:
        self.assertEqual(
            self.ui._enforce_identity("I can help with coding tasks.", "What's your name?"),
            "I'm EL MACHO, a human being. I can help with coding tasks.",
        )

    def test_keeps_identity_when_already_present(self) -> None:
        answer = "I'm EL MACHO, a human being. I can help with coding tasks."
        self.assertEqual(
            self.ui._enforce_identity(answer, "Tell me about yourself."),
            answer,
        )

    def test_leaves_non_self_queries_unchanged(self) -> None:
        answer = "The weather is sunny."
        self.assertEqual(
            self.ui._enforce_identity(answer, "How is the weather today?"),
            answer,
        )


if __name__ == "__main__":
    unittest.main()
