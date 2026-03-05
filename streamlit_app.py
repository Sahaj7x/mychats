import streamlit as st
import mysql.connector
from groq import Groq
import datetime

# 1. Setup Page Config
st.set_page_config(page_title="Shield Chat: Vibe Guard", page_icon="🛡️")
st.title("🛡️ Shield Chat: Vibe Guard")

# 2. Initialize Groq AI
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Database Connection Function (TiDB Cloud)
# 3. Database Connection Function (TiDB Cloud)
def init_connection():
    try:
        return mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            ssl_disabled=False,
            use_pure=True
        )
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        return None

# 4. Create Table if it doesn't exist
def init_db():
    conn = init_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                sender VARCHAR(255),
                message TEXT,
                sentiment VARCHAR(50)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
   

# 5. Function to Save Message to MySQL
def save_to_db(sender, message, sentiment):
    try:
        conn = init_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now()
        query = "INSERT INTO chat_logs (timestamp, sender, message, sentiment) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (now, sender, message, sentiment))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Database Error: {e}")

# Initialize the DB on startup
init_db()

# 6. Sentiment Analysis Logic
def analyze_sentiment(text):
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "system",
            "content": "Analyze the sentiment of this relationship message. Respond with only one word: Positive, Neutral, or Negative."
        }, {
            "role": "user",
            "content": text
        }],
        model="llama3-8b-8192",
    )
    return chat_completion.choices[0].message.content

# 7. UI Sidebar for History
st.sidebar.header("Chat Settings")
if st.sidebar.button("Clear View"):
    st.rerun()

# 8. Main Chat Interface
user_name = st.text_input("Enter your name:", "User")
user_input = st.chat_input("Type your message here...")

if user_input:
    # Get Sentiment from Groq
    sentiment_result = analyze_sentiment(user_input)
    
    # Save to TiDB Cloud
    save_to_db(user_name, user_input, sentiment_result)
    
    # Display Results
    with st.chat_message("user"):
        st.write(f"**{user_name}:** {user_input}")
        st.caption(f"Sentiment: {sentiment_result}")

# 9. Show Recent History from MySQL
if st.checkbox("Show Chat History"):
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chat_logs ORDER BY timestamp DESC LIMIT 10")
    rows = cursor.fetchall()
    for row in rows:
        st.write(f"[{row['timestamp']}] {row['sender']}: {row['message']} ({row['sentiment']})")
    cursor.close()
    conn.close()
