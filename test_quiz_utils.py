import unittest

from quiz_utils import get_system_prompt, get_video_id, is_youtube_url


class GetVideoIdTests(unittest.TestCase):
    def test_extracts_id_from_watch_url_with_other_parameters(self):
        self.assertEqual(
            get_video_id("https://www.youtube.com/watch?list=PL123&v=Abc_123-XyZ&t=30"),
            "Abc_123-XyZ",
        )

    def test_extracts_id_from_short_and_embed_urls(self):
        self.assertEqual(get_video_id("https://youtu.be/Abc_123-XyZ?t=30"), "Abc_123-XyZ")
        self.assertEqual(
            get_video_id("https://www.youtube-nocookie.com/embed/Abc_123-XyZ"),
            "Abc_123-XyZ",
        )

    def test_rejects_non_youtube_hosts_and_malformed_ids(self):
        for url in (
            "https://example.com/watch?v=Abc_123-XyZ",
            "https://youtube.com.evil.example/watch?v=Abc_123-XyZ",
            "https://youtube.com/watch?v=too-short",
            "not a URL",
            None,
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                get_video_id(url)

    def test_youtube_detection_uses_the_same_validated_formats(self):
        self.assertTrue(is_youtube_url("https://youtube.com/shorts/Abc_123-XyZ"))
        self.assertFalse(is_youtube_url("https://example.com/watch?v=Abc_123-XyZ"))


class SystemPromptTests(unittest.TestCase):
    def test_prompt_includes_requested_count_and_difficulty(self):
        prompt = get_system_prompt("hard", 7)
        self.assertIn("Create exactly 7 multiple-choice questions", prompt)
        self.assertIn("Difficulty level: HARD", prompt)
        self.assertIn("deep analysis, synthesis, and critical thinking", prompt)

    def test_unknown_difficulty_uses_medium_guidance(self):
        prompt = get_system_prompt("custom", 5)
        self.assertIn("Difficulty level: CUSTOM", prompt)
        self.assertIn("moderately challenging questions", prompt)


if __name__ == "__main__":
    unittest.main()
