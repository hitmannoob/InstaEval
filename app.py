from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import os
from pydantic import BaseModel
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import json
from quiz_utils import (
    get_system_prompt,
    get_video_id,
    is_youtube_url,
    validate_quiz_request,
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

api_key = os.getenv("OPENAI_API_KEY")



class MyModel(BaseModel):
    question: str
    options: List[str]
    answer: str

class Answer(BaseModel):
    quiz: List[MyModel]

def get_transcript_text(video_url):
    try:
        video_id = get_video_id(video_url)
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        full_text = "\n".join([entry.text for entry in transcript])
        return full_text
    except Exception as e:
        print(f"Transcript extraction error: {str(e)}")
        return None

@app.route("/generate_quiz", methods=["POST", "OPTIONS"])
@cross_origin()
def generate_quiz():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True)
    validated, validation_error = validate_quiz_request(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    url = validated["url"]
    text = validated["text"]
    level = validated["level"]
    num_questions = validated["num_questions"]
    
    # Handle YouTube URLs
    if is_youtube_url(url):
        print(f"Processing YouTube URL: {url}")
        content_text = get_transcript_text(url)
        if not content_text:
            error_msg = "Could not extract YouTube transcript. The video may not have captions enabled or may be restricted."
            print(f"Error: {error_msg}")
            return jsonify({"error": error_msg, "suggestion": "Try a different YouTube video with captions enabled"}), 400
    # Handle direct text
    elif text:
        print(f"Processing text content, length: {len(text)}")
        content_text = text
    else:
        error_msg = "No URL or text provided"
        return jsonify({"error": error_msg}), 400
    
    # Limit text length to avoid token limits
    max_chars = 30000
    if len(content_text) > max_chars:
        content_text = content_text[:max_chars]
    
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY is not configured"}), 503

    try:
        client = OpenAI(api_key=api_key)
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": get_system_prompt(level, num_questions)
                },
                {
                    "role": "user",
                    "content": f"Generate quiz questions from this content:\n\n{content_text}"
                }
            ],
            response_format=Answer
        )
        
        quiz_content = completion.choices[0].message.content
        print(f"Generated quiz successfully - Level: {level}, Questions: {num_questions}")
        
        if quiz_content is None:
            return jsonify({"error": "Empty response from AI"}), 500
        
        quiz_json = json.loads(quiz_content)
        return jsonify({"quiz": quiz_json['quiz']}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
