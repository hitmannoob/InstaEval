from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import os
from pydantic import BaseModel
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi
import re
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

api_key = os.getenv("OPENAI_API_KEY")



def get_system_prompt(level, num_questions):
    difficulty_instructions = {
        "easy": "Create simple, straightforward questions testing basic recall and understanding.",
        "medium": "Create moderately challenging questions that test understanding and application of concepts.",
        "hard": "Create complex questions that require deep analysis, synthesis, and critical thinking."
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

class MyModel(BaseModel):
    question: str
    options: List[str]
    answer: str

class Answer(BaseModel):
    quiz: List[MyModel]

def get_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL")

def get_transcript_text(video_url):
    video_id = get_video_id(video_url)
    try: 
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
    
    data = request.get_json()
    print(f"Received data: {data}")  # Debug log
    
    url = data.get('url')
    text = data.get('text')
    level = data.get('level', 'medium')  # Default to medium if not provided
    num_questions = data.get('numQuestions', 10)  # Default to 10 if not provided
    
    # Validate inputs
    if level not in ['easy', 'medium', 'hard']:
        level = 'medium'
    if not isinstance(num_questions, int) or num_questions < 5 or num_questions > 20:
        num_questions = 10
    
    # Handle YouTube URLs
    if url and 'youtube.com/watch' in url:
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
        print(f"Error: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    # Limit text length to avoid token limits
    max_chars = 30000
    if len(content_text) > max_chars:
        content_text = content_text[:max_chars]
    
    client = OpenAI(api_key=api_key)
    
    try:
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