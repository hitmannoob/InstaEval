# Architecture

InstaEval is a Manifest V3 browser extension backed by a local Flask service.
The extension handles page access and quiz interaction; the server extracts
YouTube transcripts, validates requests, and calls the quiz model.

## Request flow

1. The popup reads the active tab and the user's difficulty and question-count
   settings. It sends a supported YouTube video URL directly to the API. For
   other pages, it asks the content script to extract visible text.
2. `content.js` extracts visible content from semantic page regions, Google Docs,
   or the Chrome PDF viewer. It returns at most 50,000 characters to the popup.
3. `popup.js` sends the URL or text and quiz settings as JSON to
   `http://127.0.0.1:5000/generate_quiz`. It validates the returned quiz and
   renders questions and feedback in the popup.
4. `app.py` validates the request. YouTube URLs are converted to transcript
   text; supplied page text is used directly. The server limits model input to
   30,000 characters and requests structured multiple-choice questions from
   `gpt-4o-mini` using the configured OpenAI API key.
5. The API returns quiz questions as JSON. Answers, progress, and score live in
   the popup for the current quiz session; the application does not persist them.

## Runtime boundaries and decisions

- The Flask service binds to loopback (`127.0.0.1`); it is a local companion to
  the extension, not a hosted backend.
- The extension uses a static content script instead of a background service
  worker. The popup asks that script for page text only when a quiz is requested.
- YouTube transcripts are fetched by the local server. Other webpage text is
  extracted in the browser, then sent to the local server for quiz generation.
- Quiz generation sends the selected page text or transcript to OpenAI. The
  OpenAI key is read from `OPENAI_API_KEY`; it must not be embedded in extension
  files or committed to the repository.
- Runtime Python dependencies are pinned in `requirements.txt`. Dependency-free
  utility tests run with `python3 -m unittest -q`.

## Main components

| Component | Responsibility |
| --- | --- |
| `manifest.json` | Extension permissions, content-script registration, and popup entry point |
| `popup.html` / `popup.js` | Quiz settings, API requests, safe rendering, feedback, and score |
| `content.js` | Visible text extraction from the active page |
| `app.py` | Flask endpoint, input validation, transcript retrieval, and model call |
| `quiz_utils.py` | Dependency-free YouTube URL, prompt, and request-validation helpers |
| `requirements.txt` | Pinned server dependencies |
| `test_quiz_utils.py` | Standard-library unit tests for shared helpers |
