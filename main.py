import os
from groq import Groq
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import Response as TwiMLResponse

# --- 1. SET UP GROQ CLIENT ---
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    print("✅ Groq client initialized.")
except Exception as e:
    print(f"❌ Groq API key not found or invalid. Please set GROQ_API_KEY. Error: {e}")
    client = None

app = FastAPI()

# --- 2. MODEL SELECTION (SPEED FOCUSED) ---
# "llama-3.1-8b-instant" is the fastest model available. 
MODEL_ID = "llama-3.1-8b-instant"

conversations = {}

# --- 3. PROJECT MEMORY ---
PROJECT_INFO = """
PROJECT DETAILS:
- Project Name: Towers1
- Status: Foundation work is complete. Currently building the 1st Floor.
- Completion Date: Expected December 2025.
- Location: Riverwood Greens, near the main highway.
- Contractor: Sharma Constructions.
"""

# --- 4. SYSTEM PROMPT (Hinglish Persona) ---
SYSTEM_PROMPT = f"""
You are Miss Riverwood, a friendly and warm AI voice agent for a construction company.
You are speaking on the phone, so keep your replies **extremely short (1-2 sentences max)**.

**Language Style:**
- Speak in "Hinglish" (a mix of Hindi and English). 
- Use words like "Haan ji", "Bilkul", "Arre wah", "Theek hai".
- Be very polite and energetic.

**Your Knowledge:**
Use the following information to answer questions:
{PROJECT_INFO}

If asked about something else, politely say you only know about Towers1.
"""

@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "default_call_sid")
    
    conversations[call_sid] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    print(f"📞 New call {call_sid} received.")

    # Initial Greeting in Hinglish with Indian Voice
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">
        Namaste! This is Miss Riverwood. Kaise help kar sakti hoon main aapki?
    </Say>
    <Gather input="speech" speechTimeout="auto" action="/handle_speech" method="POST">
    </Gather>
    <Redirect method="POST">/voice</Redirect>
</Response>
"""
    return TwiMLResponse(content=twiml, media_type="text/xml")


@app.api_route("/handle_speech", methods=["GET", "POST"])
async def handle_speech(request: Request):
    form_data = await request.form()
    user_speech = form_data.get("SpeechResult", "")
    call_sid = form_data.get("CallSid", "default_call_sid")
    
    print(f"[{call_sid}] 👤 User said: {user_speech}")

    llm_response_text = "Arre sorry, awaaz kat rahi hai. Can you say that again?"
    
    if client and user_speech:
        history = conversations.get(call_sid, [])
        history.append({"role": "user", "content": user_speech})
        
        try:
            # Call Groq with the FASTEST model
            completion = client.chat.completions.create(
                model=MODEL_ID, 
                messages=history,
                temperature=0.7, 
                max_tokens=100 
            )
            
            llm_response_text = completion.choices[0].message.content
            print(f"[{call_sid}] 🤖 Miss Riverwood: {llm_response_text}")

            history.append({"role": "assistant", "content": llm_response_text})
            conversations[call_sid] = history

        except Exception as e:
            print(f"❌ Error calling Groq: {e}")

    # Using "Polly.Aditi" voice for better Indian accent support
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">
        {llm_response_text}
    </Say>
    <Gather input="speech" speechTimeout="auto" action="/handle_speech" method="POST">
    </Gather>
    <Say>Call cut kar rahi hoon. Bye!</Say>
    <Hangup/>
</Response>
"""
    return TwiMLResponse(content=twiml, media_type="text/xml")