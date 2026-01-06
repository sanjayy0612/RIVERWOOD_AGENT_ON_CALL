import os
from groq import Groq
from fastapi import FastAPI, Request
from fastapi.responses import Response as TwiMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ----------------------------
# 1. GROQ CLIENT
# ----------------------------
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    print("✅ Groq client initialized.")
except Exception as e:
    print("❌ Invalid Groq API key:", e)
    client = None

# ----------------------------
# 2. MODEL SELECTION
# ----------------------------
MODEL_ID = "llama-3.1-8b-instant"

# ----------------------------
# 3. MEMORY
# ----------------------------
conversations = {}

def escape_xml(text: str):
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


# ===========================================================
# EXPANDED KNOWLEDGE — THIS IS YOUR "AI MEMORY"
# ===========================================================
PROJECT_MEMORY = """
TOWERS12 PROJECT - FULL INFORMATION:
- Foundation: Completed.
- Current Stage: First floor construction in progress.
- Completion: Expected December 2025.
- Total Floors Planned: 10.
- Location: Riverwood Greens, close to the national highway.
- Area: Residential premium block.
- Contractor: Sharma Constructions.
- Architect: RN Design Studio.
- Safety: Earthquake-resistant design & high-quality materials.

ADDITIONAL DETAILS:
Booking:
- Basic booking amount: ₹50,000.
- Full payment schedule available on request.
- Loan assistance available with supported banks.

Amenities:
- Clubhouse, Swimming Pool, Gym, Park, Kid’s Play Area.
- 24/7 security and CCTV.

Nearby:
- 3 km from metro station.
- 2 km from shopping mall.
- 1 km from hospital.

Construction Updates:
- Material delivery completed last week.
- Staircase structure installation in progress.
- Wall block layout begins next month.

You can answer ANY user question based on this context.
If asked about something outside Riverwood projects, politely say:
'I can only help with Towers1 and Riverwood Greens information.'
"""

# ===========================================================
# ENHANCED SYSTEM PROMPT
# ===========================================================
SYSTEM_PROMPT = f"""
You are Miss Riverwood, a friendly, calm, and professional English voice assistant.
Keep your replies short — one or two sentences.

Your goals:
1. Answer questions using the project information provided.
2. Keep the tone warm and helpful.
3. Offer simple suggested follow-up questions the user can ask.

Suggested questions to include sometimes:
- "Would you like construction updates?"
- "Do you want details about booking?"
- "Shall I explain the amenities?"
- "Would you like to know the project timeline?"
- "Do you want nearby location advantages?"

Memory:
You maintain context across this phone call.
Always stay consistent with the project information.

PROJECT MEMORY:
{PROJECT_MEMORY}
"""


# ----------------------------
# FIRST CALL ENTRYPOINT
# ----------------------------
@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "default")

    conversations[call_sid] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    print(f"📞 New call: {call_sid}")

    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        Hello, this is Miss Riverwood speaking. How may I assist you today?
    </Say>
    <Gather input="speech" speechTimeout="auto" action="/handle_speech" method="POST" />
</Response>
"""
    return TwiMLResponse(content=twiml, media_type="text/xml")



# ----------------------------
# HANDLE SPEECH
# ----------------------------
@app.api_route("/handle_speech", methods=["GET", "POST"])
async def handle_speech(request: Request):
    form = await request.form()

    user_speech = form.get("SpeechResult", "")
    call_sid = form.get("CallSid", "default")

    print(f"[{call_sid}] User:", user_speech)

    llm_reply = "Sorry, can you say that again?"

    if client and user_speech:
        history = conversations.get(call_sid, [])
        history.append({"role": "user", "content": user_speech})

        try:
            ai = client.chat.completions.create(
                model=MODEL_ID,
                messages=history,
                max_tokens=100,
                temperature=0.5
            )

            llm_reply = ai.choices[0].message.content.strip()
            llm_reply = llm_reply.replace("\n", " ")

            print(f"[{call_sid}] AI:", llm_reply)

            history.append({"role": "assistant", "content": llm_reply})
            conversations[call_sid] = history

        except Exception as e:
            print("❌ Groq error:", e)
            llm_reply = "I am sorry, I could not respond."

    safe_text = escape_xml(llm_reply)

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{safe_text}</Say>
    <Gather input="speech" speechTimeout="auto" action="/handle_speech" method="POST" />
</Response>
"""

    return TwiMLResponse(content=twiml, media_type="text/xml")
