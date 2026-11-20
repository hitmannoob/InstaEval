import unittest

from quiz_utils import (
    get_system_prompt,
    get_video_id,
    is_youtube_url,
    validate_quiz_request,
)


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


class ValidateQuizRequestTests(unittest.TestCase):
    def test_normalizes_defaults_and_trims_content(self):
        request, error = validate_quiz_request({"text": "  lesson notes  "})

        self.assertIsNone(error)
        self.assertEqual(request, {
            "url": None,
            "text": "lesson notes",
            "level": "medium",
            "num_questions": 10,
        })

    def test_rejects_non_object_and_wrong_content_types(self):
        for data, message in (
            (None, "Request body must be a JSON object"),
            (["text"], "Request body must be a JSON object"),
            ({"text": 12}, "text must be a string"),
            ({"url": 12}, "url must be a string"),
        ):
            with self.subTest(data=data):
                request, error = validate_quiz_request(data)
                self.assertIsNone(request)
                self.assertEqual(error, message)

    def test_rejects_invalid_level_and_question_counts(self):
        for data, message in (
            ({"level": "expert"}, "level must be easy, medium, or hard"),
            ({"level": 2}, "level must be easy, medium, or hard"),
            ({"numQuestions": True}, "numQuestions must be an integer between 5 and 20"),
            ({"numQuestions": 4}, "numQuestions must be an integer between 5 and 20"),
            ({"numQuestions": 21}, "numQuestions must be an integer between 5 and 20"),
            ({"numQuestions": "10"}, "numQuestions must be an integer between 5 and 20"),
        ):
            with self.subTest(data=data):
                request, error = validate_quiz_request(data)
                self.assertIsNone(request)
                self.assertEqual(error, message)

    def test_accepts_question_count_boundaries(self):
        for count in (5, 20):
            with self.subTest(count=count):
                request, error = validate_quiz_request({"numQuestions": count})
                self.assertIsNone(error)
                self.assertEqual(request["num_questions"], count)


if __name__ == "__main__":
    unittest.main()
