import streamlit as st
import mysql.connector
from groq import Groq
import datetime

# 1. Secret & AI Setup
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def init_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        ssl_disabled=False,
        use_pure=True
    )

# 2. Get the Latest Vibe for the Status Bar
last_vibe = "Neutral"
conn = init_connection()
if conn:
    cursor = conn.cursor()
    cursor.execute("SELECT sentiment FROM chat_logs ORDER BY id DESC LIMIT 1")
    res = cursor.fetchone()
    if res: last_vibe = res[0]
    cursor.close()
    conn.close()

# 3. WhatsApp Mobile CSS
vibe_colors = {"Positive": "#128C7E", "Negative": "#af2d2d", "Neutral": "#075E54"}
current_color = vibe_colors.get(last_vibe, "#075E54")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0b141a; }}
    /* Header / Status Bar */
    .header {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: {current_color}; color: white;
        padding: 15px; z-index: 1000; transition: 1s;
        font-weight: bold; box-shadow: 0px 2px 5px rgba(0,0,0,0.5);
    }}
    /* Chat Bubbles */
    .bubble {{
        padding: 10px 15px; border-radius: 15px; margin: 8px;
        max-width: 80%; position: relative; font-size: 16px; line-height: 1.4;
    }}
    .sent {{ background-color: #005c4b; color: white; align-self: flex-end; margin-left: auto; }}
    .received {{ background-color: #202c33; color: white; align-self: flex-start; }}
    .time {{ font-size: 10px; opacity: 0.6; text-align: right; margin-top: 4px; display: block; }}
    .chat-container {{ display: flex; flex-direction: column; margin-top: 70px; margin-bottom: 100px; }}
    </style>
    <div class="header">🛡️ Shield Chat <br> <span style="font-size:12px; font-weight:normal;">Vibe: {last_vibe}</span></div>
    """, unsafe_allow_html=True)

# 4. Display Messages
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
conn = init_connection()
if conn:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT message, sentiment, timestamp FROM chat_logs ORDER BY timestamp DESC LIMIT 15")
    for row in reversed(cursor.fetchall()):
        align_class = "received" # For analysis targets
        time_str = row['timestamp'].strftime("%I:%M %p")
        st.markdown(f'''
            <div class="bubble {align_class}">
                {row['message']}
                <span class="time">{time_str}</span>
            </div>
            ''', unsafe_allow_html=True)
    cursor.close()
    conn.close()
st.markdown('</div>', unsafe_allow_html=True)

# 5. Fixed Input Bar
user_input = st.chat_input("Paste message to analyze...")

if user_input:
    # Analyze with Llama 3.3
    chat_completion = client.chat.completions.create(
        messages=[{"role": "system", "content": "Respond with one word: Positive, Neutral, or Negative."},
                  {"role": "user", "content": user_input}],
        model="llama-3.3-70b-versatile"
    )
    sentiment = chat_completion.choices[0].message.content
    
    # Save & Rerun
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_logs (timestamp, sender, message, sentiment) VALUES (%s, %s, %s, %s)",
                   (datetime.datetime.now(), "User", user_input, sentiment))
    conn.commit()
    cursor.close()
    conn.close()
    st.rerun()
