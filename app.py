import streamlit as st
import os
import asyncio
import edge_tts
from tavily import TavilyClient
import google.generativeai as genai
from dotenv import load_dotenv

# --- 1. SECURE CONFIGURATION ---
load_dotenv()

# Safe Secret Loading Logic
def get_secret(key):
    # 1. Try Streamlit Cloud Secrets first
    try:
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass
    # 2. Fallback to local .env file
    return os.getenv(key)

GEMINI_KEY = get_secret("GEMINI_API_KEY")
TAVILY_KEY = get_secret("TAVILY_API_KEY")

if GEMINI_KEY and TAVILY_KEY:
    genai.configure(api_key=GEMINI_KEY)
    tavily = TavilyClient(api_key=TAVILY_KEY)
else:
    st.error("🔑 API Keys missing! Ensure they are in your .env file locally.")
    st.stop() # Stops the app here so it doesn't crash later

# --- 2. INTELLIGENCE ENGINE ---
def get_targeted_intel(query, category="General"):
    """Scrapes authoritative sources and synthesizes a brief."""
    # Targeting India Today and major global news outlets
    search_query = f"site:indiatoday.in OR site:reuters.com OR site:bloomberg.com {query} {category} news April 2026"
    
    try:
        search = tavily.search(query=search_query, search_depth="advanced", max_results=5)
        context = "\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in search['results']])
        
        prompt = f"""
        You are a Senior Geopolitical Analyst. Answer: '{query}'
        Category: {category} | Date: April 3, 2026
        
        Context:
        {context}
        
        Structure for an AUDIO BRIEF:
        1. THE FLASHPOINT: Latest fact/price from the sources.
        2. BUSINESS IMPACT: Impact on Energy, Tech, or Markets.
        3. THE INDIA ANGLE: Specific relevance to the Indian economy.
        4. BOTTOM LINE: 48-hour forecast.
        
        Keep it professional, under 150 words.
        """
        # Using gemini-2.0-flash for 2026 speed/accuracy
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Intelligence Error: {str(e)}"

async def generate_audio(text):
    """Converts report to professional audio."""
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
    await communicate.save("brief.mp3")

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="GeoPulse AI", layout="wide", page_icon="🌍")

# Sidebar History
if 'history' not in st.session_state: st.session_state.history = []
with st.sidebar:
    st.title("📜 Intelligence Log")
    for h in st.session_state.history[:5]:
        st.caption(f"🕒 {h}")
    st.divider()
    st.info("GeoPulse v1.0 | 2026")

# Main Title
st.title("🌍 GeoPulse AI Command Center")
st.caption("Targeted Intelligence for Busy Professionals")

# --- 4. CATEGORY TILES ---
st.write("### 📂 Quick Categories")
cols = st.columns(4)
if "active_cat" not in st.session_state: st.session_state.active_cat = "General"

with cols[0]: 
    if st.button("📈 Markets", use_container_width=True): st.session_state.active_cat = "Markets"
with cols[1]: 
    if st.button("⚔️ Geopolitics", use_container_width=True): st.session_state.active_cat = "Geopolitics"
with cols[2]: 
    if st.button("🇮🇳 India Today", use_container_width=True): st.session_state.active_cat = "India National"
with cols[3]: 
    if st.button("🔋 Energy", use_container_width=True): st.session_state.active_cat = "Energy"

st.info(f"Targeting: **{st.session_state.active_cat}**")

# --- 5. HANDS-FREE INPUT ---
st.write("---")
# Native high-performance audio widget
audio_command = st.audio_input("🎙️ Record Voice Briefing Request")
text_command = st.chat_input("Or type your query (e.g., 'Gold rate hike chances')...")

# --- 6. EXECUTION LOGIC ---
final_query = None

if text_command:
    final_query = text_command
elif audio_command:
    # Trigger a summary of the active category if voice is detected
    final_query = f"Latest briefing on {st.session_state.active_cat}"

if final_query:
    st.session_state.history.insert(0, final_query)
    with st.spinner(f"Scraping {st.session_state.active_cat} intelligence..."):
        report = get_targeted_intel(final_query, st.session_state.active_cat)
        
        # Display Text
        st.chat_message("assistant").write(report)
        
        # Generate and Play Audio
        try:
            asyncio.run(generate_audio(report))
            st.audio("brief.mp3", format="audio/mp3", autoplay=True)
            st.success("✅ Briefing complete.")
        except:
            st.warning("Audio playback failed, but text is ready.")