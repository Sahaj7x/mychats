import streamlit as st
from streamlit_gsheets import GSheetsConnection
from groq import Groq
import pandas as pd
from datetime import datetime

# 1. Page Setup
st.set_page_config(page_title="Shield Chat", page_icon="🛡️")
st.title("🛡️ Shield Chat: Vibe Guard")

# 2. Connect to Google Sheets & Groq
conn = st.connection("gsheets", type=GSheetsConnection)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Load Chat History from Google Sheets
def load_data():
    return conn.read(worksheet="Sheet1", usecols=[0, 1, 2], ttl=0)

data = load_data()

# 4. Sidebar for User Selection
user = st.sidebar.radio("Who is chatting?", ["Sachu", "Partner"])

# 5. Display WhatsApp-style Chat History
st.subheader("💬 Conversation History")
for index, row in data.iterrows():
    with st.chat_message("user" if row['name'] == "Sachu" else "assistant"):
        st.write(f"**{row['name']}**: {row['message']}")
        st.caption(f"{row['timestamp']}")

# 6. Chat Input & AI Vibe Check
if prompt := st.chat_input("Type your message..."):
    # AI Vibe Check logic
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a relationship mediator. If the user's message is aggressive, warn them. If it is calm, say 'SAFE'."},
            {"role": "user", "content": prompt}
        ],
        model="llama3-8b-8192",
    )
    
    response = chat_completion.choices[0].message.content

    if "SAFE" in response.upper():
        # Save to Google Sheets if it's safe
        new_row = pd.DataFrame([{
            "name": user,
            "message": prompt,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        updated_df = pd.concat([data, new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Message Sent & Saved!")
        st.rerun()
    else:
        st.error(f"⚠️ Vibe Check Warning: {response}")
