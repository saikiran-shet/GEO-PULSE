import streamlit as st
import os
import asyncio
import edge_tts
from tavily import TavilyClient
import google.generativeai as genai
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- 2. THE INTELLIGENCE ENGINE ---
def get_targeted_intel(query, category="General"):
    # Targeted scraping: focusing on high-authority news
    search_query = f"site:indiatoday.in OR site:reuters.com {query} {category} news April 2026"
    search = tavily.search(query=search_query, search_depth="advanced", max_results=5)
    context = "\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in search['results']])
    
    prompt = f"""
    Context (April 2026): {context}
    User Query: {query}
    Category: {category}
    
    Task: Provide a high-level 'Executive Brief'. 
    Focus: 1. Latest Headline 2. Business/Market Impact 3. 48-hour Outlook.
    Keep it professional and under 150 words.
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    return model.generate_content(prompt).text

async def text_to_speech(text):
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
    await communicate.save("response.mp3")

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="GeoPulse AI", layout="wide")

if 'history' not in st.session_state: st.session_state.history = []

# Sidebar
with st.sidebar:
    st.title("📜 Intelligence Log")
    for h in st.session_state.history[:5]: st.caption(f"🕒 {h}")

st.title("🌍 GeoPulse Command Center")

# --- 4. CATEGORY TILES ---
st.write("### 📂 Choose Category")
cols = st.columns(4)
selected_cat = "General"

# Using a session state to track the active category
if "active_cat" not in st.session_state: st.session_state.active_cat = "General"

with cols[0]: 
    if st.button("📈 Markets", use_container_width=True): st.session_state.active_cat = "Markets"
with cols[1]: 
    if st.button("⚔️ Geopolitics", use_container_width=True): st.session_state.active_cat = "Geopolitics"
with cols[2]: 
    if st.button("🇮🇳 India Today", use_container_width=True): st.session_state.active_cat = "India National"
with cols[3]: 
    if st.button("🔋 Energy", use_container_width=True): st.session_state.active_cat = "Energy"

st.info(f"Current Mode: **{st.session_state.active_cat}**")

# --- 5. THE NEW HANDS-FREE WIDGET ---
st.write("---")
# Native Streamlit Audio Input (Replaces all buggy plugins)
audio_input = st.audio_input("🎙️ Record Voice Command")
chat_input = st.chat_input("Or type your briefing request...")

# --- 6. PROCESSING LOGIC ---
final_query = None

# If user recorded audio
if audio_input:
    # In a full build, we'd send 'audio_input' to Gemini/Whisper for transcription.
    # For now, let's trigger a category-based summary.
    final_query = f"Latest news on {st.session_state.active_cat}"

# If user typed
if chat_input:
    final_query = chat_input

if final_query:
    st.session_state.history.insert(0, final_query)
    with st.spinner(f"Scraping global intelligence for {st.session_state.active_cat}..."):
        report = get_targeted_intel(final_query, st.session_state.active_cat)
        
        st.chat_message("assistant").write(report)
        
        # Audio Response
        asyncio.run(text_to_speech(report))
        st.audio("response.mp3", format="audio/mp3", autoplay=True)