"""Dependency-free helpers shared by InstaEval's API and unit tests."""

import json
from urllib.parse import parse_qs, urlparse


_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
    "youtu.be",
    "www.youtu.be",
}
_VIDEO_ID_LENGTH = 11


def get_video_id(url):
    """Return the video ID from a supported YouTube URL, or raise ValueError."""
    if not isinstance(url, str):
        raise ValueError("Invalid YouTube URL")

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_HOSTS:
        raise ValueError("Invalid YouTube URL")

    video_id = None
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/", 1)[0]
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [None])[0]
    else:
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 2 and parts[0] in {"embed", "shorts", "live", "v"}:
            video_id = parts[1]

    if (not video_id or len(video_id) != _VIDEO_ID_LENGTH
            or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                   for char in video_id)):
        raise ValueError("Invalid YouTube URL")
    return video_id


def is_youtube_url(url):
    """Return whether a URL is a supported YouTube video URL."""
    try:
        get_video_id(url)
    except ValueError:
        return False
    return True


def validate_quiz_request(data):
    """Validate API request data and return normalized fields plus an error."""
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    url = data.get("url")
    text = data.get("text")
    if url is not None and not isinstance(url, str):
        return None, "url must be a string"
    if text is not None and not isinstance(text, str):
        return None, "text must be a string"

    level = data.get("level", "medium")
    if not isinstance(level, str) or level not in {"easy", "medium", "hard"}:
        return None, "level must be easy, medium, or hard"

    num_questions = data.get("numQuestions", 10)
    if (isinstance(num_questions, bool) or not isinstance(num_questions, int)
            or not 5 <= num_questions <= 20):
        return None, "numQuestions must be an integer between 5 and 20"

    normalized_url = url.strip() if url else ""
    normalized_text = text.strip() if text else ""
    return {
        "url": normalized_url or None,
        "text": normalized_text or None,
        "level": level,
        "num_questions": num_questions,
    }, None


def validate_generated_quiz(quiz, expected_count):
    """Validate and normalize the model's MCQs before returning them to clients."""
    if not isinstance(quiz, list) or len(quiz) != expected_count:
        return None, "Quiz must contain the requested number of questions"

    validated_questions = []
    for question in quiz:
        if not isinstance(question, dict):
            return None, "Each question must be an object"

        prompt = question.get("question")
        options = question.get("options")
        answer = question.get("answer")
        if not isinstance(prompt, str) or not prompt.strip():
            return None, "Each question must have non-empty text"
        if (not isinstance(options, list) or len(options) != 4
                or any(not isinstance(option, str) or not option.strip() for option in options)):
            return None, "Each question must have exactly four non-empty text options"
        if not isinstance(answer, str) or answer.strip().upper() not in {"A", "B", "C", "D"}:
            return None, "Each answer must be one of A, B, C, or D"

        validated_questions.append({
            "question": prompt.strip(),
            "options": [option.strip() for option in options],
            "answer": answer.strip().upper(),
        })

    return validated_questions, None


def parse_generated_quiz(response_content, expected_count):
    """Parse a model response and validate its quiz structure and question count."""
    if not isinstance(response_content, str) or not response_content.strip():
        return None, "The model returned an empty response"
    try:
        response = json.loads(response_content)
    except json.JSONDecodeError:
        return None, "The model response was not valid JSON"

    raw_quiz = response.get("quiz") if isinstance(response, dict) else None
    return validate_generated_quiz(raw_quiz, expected_count)


def get_system_prompt(level, num_questions):
    """Build the instruction sent to the quiz generation model."""
    difficulty_instructions = {
        "easy": "Create simple, straightforward questions testing basic recall and understanding.",
        "medium": "Create moderately challenging questions that test understanding and application of concepts.",
        "hard": "Create complex questions that require deep analysis, synthesis, and critical thinking.",
    }

    return f"""You are a domain expert and an educational content creator. Your job is to generate high-quality quiz questions from the provided text content.

    Guidelines:
    - Extract key facts, definitions, concepts, or insights from the text.
    - Create exactly {num_questions} multiple-choice questions (MCQs)
    - Difficulty level: {level.upper()}
    - {difficulty_instructions.get(level, difficulty_instructions['medium'])}
    - Ensure that each question:
        - Is concise and clearly worded.
        - Has only one correct answer.
        - Tests understanding appropriate to the difficulty level.
    - Each question should have exactly 4 options, labeled A, B, C, D.

    Return the questions in the following format:
    [
    {{
        "question": "Your question here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "A"
    }},
    ...
    ]"""
