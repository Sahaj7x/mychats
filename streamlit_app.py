import streamlit as st
import re
from datetime import datetime
from groq import Groq

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        /* This makes the top bar disappear on mobile */
        .stAppDeployButton {display:none;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

st.set_page_config(
    page_title="Shield Chat", 
    page_icon="🎀", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)
# --- 1. CONFIGURATION ---
# IMPORTANT: Replace with your actual Groq key
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Mobile Page Config
st.set_page_config(page_title="Shield Chat", page_icon="🛡️")

# Initialize Session States (Memory)
if "warning_score" not in st.session_state:
    st.session_state.warning_score = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
if "locked" not in st.session_state:
    st.session_state.locked = False
if "current_task" not in st.session_state:
    st.session_state.current_task = ""

# --- 2. THE AI BRAIN ---
def analyze_vibe(text):
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Zero-tolerance Manglish moderator. Score 2 for insults (thendi, patti, etc) or gender superiority. Score 1 for rude tone. Score 0 for safe. Reply ONLY with the number."},
                {"role": "user", "content": text}
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=3
        )
        result = completion.choices[0].message.content.strip()
        score_match = re.search(r'\d', result)
        return int(score_match.group()) if score_match else 0
    except:
        return 0

def get_ai_task():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "Create a unique cooling task in Manglish/English (e.g. type a poem, solve a riddle). Reply ONLY instruction."}],
            model="llama-3.3-70b-versatile"
        )
        return completion.choices[0].message.content.strip()
    except:
        return "Type 'Respect all' to unlock."

# --- 3. DYNAMIC STYLING (The Thermometer) ---
status_msg = "✅ Vibe is Chill"
bg_color = "#90EE90" # Green

if st.session_state.warning_score >= 5:
    bg_color = "#8B0000" # Red
    st.session_state.locked = True
    status_msg = "🚨 LOCKED: Pass the AI Task!"
elif st.session_state.warning_score >= 3:
    bg_color = "#FFCC00" # Orange
    status_msg = "🟠 WARNING: Stop the argument!"
elif st.session_state.warning_score >= 1:
    bg_color = "#FFFF99" # Yellow
    status_msg = "⚠️ Vibe is changing..."

# Apply the background color to the whole mobile screen
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Shield Chat")
st.subheader(status_msg)

# --- 4. CHAT INTERFACE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 5. LOCK LOGIC ---
if st.session_state.locked:
    if not st.session_state.current_task:
        st.session_state.current_task = get_ai_task()
    
    st.error(f"**TASK:** {st.session_state.current_task}")
    task_input = st.text_input("Type your answer here:")
    
    if st.button("VERIFY"):
        # Quick AI Check
        verify = client.chat.completions.create(
            messages=[{"role": "system", "content": f"Task: {st.session_state.current_task}. Did user follow? Reply YES or NO."},
                      {"role": "user", "content": task_input}],
            model="llama-3.3-70b-versatile"
        )
        if "YES" in verify.choices[0].message.content.upper():
            st.session_state.warning_score = 0
            st.session_state.locked = False
            st.session_state.current_task = ""
            st.success("Unlocked! Stay chill.")
            st.rerun()
        else:
            st.error("AI rejected that. Try again.")

elif prompt := st.chat_input("Enter Message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    score = analyze_vibe(prompt)
    st.session_state.warning_score += score
    st.rerun()
