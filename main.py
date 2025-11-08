from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
# --- 1. Import Groq ---
from groq import Groq 
import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# --- 2. Instantiate Groq client ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

app = FastAPI()

# --- 3. ADDED BACK: Template configuration ---
# (Make sure your folder is named "template" (singular))
templates = Jinja2Templates(directory="template")

# --- 4. ADDED BACK: Conversation history ---
conversation_history = [
    {"role": "system", "content": "You are Miss Riverwood, a friendly AI voice agent. Speak warmly in Hinglish. Your goal is to build a bond. **Keep your replies very short, like 1-2 sentences.**"}
]

# --- 5. ADDED BACK: The missing GET / route ---
@app.get("/")
def home(request: Request):
    
    conversation_history.clear()
    conversation_history.append(
        {"role": "system", "content": "You are Miss Riverwood, a friendly AI voice agent. Speak warmly in Hinglish. Your goal is to build a bond. **Keep your replies very short, like 1-2 sentences.**"}
    )
    return templates.TemplateResponse("simple_frontend.html", {"request": request})

# --- 6. This is the updated POST /chat route ---
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_text = data.get("text")
    
    conversation_history.append({"role": "user", "content": user_text})

    # Use Groq (Llama 3) for the reply
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # <-- THIS IS THE NEW, ACTIVE MODEL
            messages=conversation_history,
            max_tokens=75,
        )
        
        reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})

    except Exception as e:
        print(f"Error calling Groq: {e}")
        return JSONResponse({"error": "Error with the AI model"}, status_code=500)

    # Convert reply to speech (ElevenLabs)
    try:
        tts_url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"  # 'Rachel' voice
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": reply,
            "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}
        }
        tts_response = requests.post(tts_url, headers=headers, json=payload)

        if tts_response.status_code == 200:
            audio_data = tts_response.content
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return JSONResponse({"reply": reply, "audio_base64": audio_base64})
        else:
            print(f"ElevenLabs Error: {tts_response.text}")
            return JSONResponse({"error": "ElevenLabs API error"}, status_code=500)

    except Exception as e:
        print(f"Error calling ElevenLabs: {e}")
        return JSONResponse({"error": "Error with the voice generation"}, status_code=500)