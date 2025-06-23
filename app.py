import streamlit as st
import requests
import json
import uuid
import os

# Set page configuration
st.set_page_config(page_title="Agriculture Chatbot", layout="wide")

st.title("🌾 Agriculture Chatbot")

# Replace with your Ngrok URL
RASA_URL = "https://d7cf-125-62-213-250.ngrok-free.app/webhooks/rest/webhook"

# Chat history storage file
CHAT_HISTORY_FILE = "chat_sessions.json"

# Ensure chat history file exists
if not os.path.exists(CHAT_HISTORY_FILE):
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump({}, file)


def load_chat_sessions():
    """Loads saved chat sessions from a JSON file."""
    try:
        with open(CHAT_HISTORY_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_chat_sessions(chat_sessions):
    """Saves chat sessions to a JSON file."""
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump(chat_sessions, file, indent=4)


def generate_chat_name(messages):
    """Generates a chat name based on the first meaningful user query."""
    if messages:
        for msg in messages:
            if msg["role"] == "user":
                first_message = msg["content"].strip()
                if first_message.lower() not in ["hi", "hello", "fine", "hey"]:
                    return first_message[:30]  # Limit name length
    return "New Chat"


# Load all chat sessions
chat_sessions = load_chat_sessions()

# Ensure a new chat starts when the app loads
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("💬 Chat Sessions")
    chat_names = {key: generate_chat_name(value) for key, value in chat_sessions.items()}
    selected_chat = st.radio("Select a chat", list(chat_names.values()), index=0 if chat_names else None)

    # Find chat key from name
    for key, name in chat_names.items():
        if name == selected_chat:
            st.session_state.current_chat = key
            break

    st.session_state.messages = chat_sessions.get(st.session_state.current_chat, [])

    # New chat button
    if st.button("🆕 New Chat"):
        new_chat_id = str(uuid.uuid4())
        chat_sessions[new_chat_id] = []
        save_chat_sessions(chat_sessions)
        st.session_state.current_chat = new_chat_id  # Switch to new chat
        st.session_state.messages = []
        st.rerun()

    # Delete chat button
    if st.button("🗑️ Delete Chat") and st.session_state.current_chat:
        del chat_sessions[st.session_state.current_chat]
        save_chat_sessions(chat_sessions)
        st.session_state.current_chat = None if not chat_sessions else list(chat_sessions.keys())[0]
        st.session_state.messages = chat_sessions.get(st.session_state.current_chat, [])
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Type your message here...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})
    chat_sessions[st.session_state.current_chat] = st.session_state.messages
    save_chat_sessions(chat_sessions)

    chat_names[st.session_state.current_chat] = generate_chat_name(st.session_state.messages)
    save_chat_sessions(chat_sessions)

    payload = {"sender": st.session_state.current_chat, "message": user_input}
    response = requests.post(RASA_URL, json=payload)

    bot_reply = ""
    if response.status_code == 200:
        bot_responses = response.json()
        for res in bot_responses:
            bot_reply += res.get("text", "") + "\n"

    if bot_reply:
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        chat_sessions[st.session_state.current_chat] = st.session_state.messages
        save_chat_sessions(chat_sessions)