import streamlit as st
import os
import asyncio
import edge_tts
from tavily import TavilyClient
import google.generativeai as genai
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text # New Import

# --- 1. SETUP ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

if GEMINI_KEY and TAVILY_KEY:
    genai.configure(api_key=GEMINI_KEY)
    tavily = TavilyClient(api_key=TAVILY_KEY)
else:
    st.error("API Keys missing in .env!")

# --- 2. INTELLIGENCE FUNCTIONS ---
def get_intel(query):
    search_query = f"{query} news business impact April 2026"
    search = tavily.search(query=search_query, search_depth="advanced", max_results=5)
    context = "\n".join([r['content'] for r in search['results']])
    
    prompt = f"""
    Analyze: '{query}' for a business professional.
    Context: {context}
    1. FLASHPOINT: What happened? 2. IMPACT: Business/Economy sectors. 3. BOTTOM LINE.
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    return model.generate_content(prompt).text

async def speak(text):
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
    await communicate.save("brief.mp3")

# --- 3. UI STRUCTURE ---
st.set_page_config(page_title="GeoPulse AI", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.title("📜 History")
    for item in st.session_state.history:
        st.caption(f"🕒 {item}")

st.title("🌍 GeoPulse AI")

# --- 4. THE HANDS-FREE TRIGGER ---
st.write("### 🎙️ Voice Command")
# This replaces the need for typing. It records, transcribes, and returns text.
v_input = speech_to_text(
    language='en',
    start_prompt="Click to Speak",
    stop_prompt="Stop Listening",
    just_once=True,
    key='STT'
)

# Quick Shortcuts (One-tap info)
st.write("---")
st.write("🚀 **Quick Briefs**")
c1, c2, c3 = st.columns(3)
btn_query = None
with c1: 
    if st.button("Gold Rate", use_container_width=True): btn_query = "Gold rate hike India"
with c2: 
    if st.button("UN Decision", use_container_width=True): btn_query = "UN decision impact India"
with c3: 
    if st.button("Nifty 50", use_container_width=True): btn_query = "Nifty 50 geopolitical impact"

# --- 5. EXECUTION ---
# Trigger if voice input exists OR a button was clicked
final_query = v_input if v_input else btn_query

if final_query:
    if final_query not in st.session_state.history:
        st.session_state.history.insert(0, final_query)
    
    with st.spinner(f"Analyzing {final_query}..."):
        report = get_intel(final_query)
        st.markdown(report)
        
        asyncio.run(speak(report))
        st.audio("brief.mp3", format="audio/mp3", autoplay=True)