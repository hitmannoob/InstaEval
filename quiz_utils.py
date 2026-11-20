"""Dependency-free helpers shared by InstaEval's API and unit tests."""

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
