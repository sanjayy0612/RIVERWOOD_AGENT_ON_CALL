# Riverwood AI Voice Agent

This is a prototype for the Riverwood AI Voice Agent Internship Challenge. It's a "bond-building" AI assistant that speaks warmly in Hinglish and can remember conversation context.

## 🚀 Tech Stack

* **Backend:** Python (FastAPI)
* **LLM:** Groq (llama-3.3-70b-versatile)
* **TTS:** ElevenLabs API
* **Frontend:** HTML, CSS, JavaScript (Browser Web Speech API)

## 🏃‍♂️ How to Run

1.  Clone this repository.
2.  Create a virtual environment: `python -m venv venv`
3.  Install dependencies: `pip install -r requirements.txt`
4.  Create a `.env` file and add your keys:
    ```
    GROQ_API_KEY=your_groq_key
    ELEVENLABS_API_KEY=your_elevenlabs_key
    ```
5.  Run the server: `uvicorn main:app --reload`
6.  Open `http://127.0.0.1:8000` in your browser.