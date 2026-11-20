import json
import unittest

from quiz_utils import (
    get_system_prompt,
    get_video_id,
    is_youtube_url,
    parse_generated_quiz,
    validate_generated_quiz,
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


class ValidateGeneratedQuizTests(unittest.TestCase):
    def setUp(self):
        self.questions = [
            {
                "question": "  First question?  ",
                "options": [" A ", "B", "C", "D"],
                "answer": "a",
            },
            {
                "question": "Second question?",
                "options": ["One", "Two", "Three", "Four"],
                "answer": "D",
            },
        ]

    def test_validates_requested_count_and_normalizes_fields(self):
        quiz, error = validate_generated_quiz(self.questions, 2)

        self.assertIsNone(error)
        self.assertEqual(quiz[0], {
            "question": "First question?",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
        })
        self.assertEqual(self.questions[0]["answer"], "a")

    def test_rejects_wrong_question_count_and_non_list_responses(self):
        for response in (None, {}, self.questions[:1], self.questions + [self.questions[0]]):
            with self.subTest(response=response):
                quiz, error = validate_generated_quiz(response, 2)
                self.assertIsNone(quiz)
                self.assertTrue(error)

    def test_rejects_malformed_question_fields(self):
        invalid_cases = (
            {"question": "", "options": ["A", "B", "C", "D"], "answer": "A"},
            {"question": "Valid?", "options": ["A", "B", "C"], "answer": "A"},
            {"question": "Valid?", "options": ["A", "B", "C", ""], "answer": "A"},
            {"question": "Valid?", "options": ["A", "B", "C", "D"], "answer": "E"},
            {"question": "Valid?", "options": ["A", "B", "C", "D"], "answer": 1},
            "not a question object",
        )
        for invalid_question in invalid_cases:
            with self.subTest(question=invalid_question):
                quiz, error = validate_generated_quiz([invalid_question, self.questions[1]], 2)
                self.assertIsNone(quiz)
                self.assertTrue(error)

    def test_parses_json_and_rejects_malformed_or_empty_responses(self):
        valid = '{"quiz": ' + json.dumps(self.questions) + "}"
        quiz, error = parse_generated_quiz(valid, 2)
        self.assertIsNone(error)
        self.assertEqual(len(quiz), 2)

        for response in (None, "", "not json", "[]", '{"quiz": []}'):
            with self.subTest(response=response):
                quiz, error = parse_generated_quiz(response, 2)
                self.assertIsNone(quiz)
                self.assertTrue(error)


if __name__ == "__main__":
    unittest.main()
