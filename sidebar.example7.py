import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import json
import os
import time
from datetime import datetime

# Folder create
CHAT_DIR = "chats"
os.makedirs(CHAT_DIR, exist_ok=True)

# OpenAI client
def get_open_ai_client():
    load_dotenv()
    return OpenAI()

client = get_open_ai_client()

# New chat
def new_chat():
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(CHAT_DIR, f"{chat_id}.json")

    messages = [
        {
            "role": "system",
            "content": (
                "You are PyMentor, a helpful Python Tutor. "
                "Answer only Python related questions. "
                "Politely refuse non Python questions."
            )
        }
    ]

    save_chat(file_path, messages)
    return chat_id

# Save chat
def save_chat(path, messages):
    with open(path, "w") as f:
        json.dump(messages, f, indent=4)

# Load chat
def load_chat(path):
    with open(path, "r") as f:
        return json.load(f)

# List chats
def list_chats():
    return sorted(os.listdir(CHAT_DIR), reverse=True)

# Delete chat
def remove_chat(chat_path):
    os.remove(chat_path)
    st.session_state.current_chat = new_chat()
    st.rerun()

# Streaming response
def stream_chat_with_ai(messages, placeholder, temperature, model):
    stream = client.responses.create(
        model=model,
        input=messages,
        temperature=temperature,
        stream=True
    )

    full_response = ""

    for event in stream:
        if event.type == "response.output_text.delta":
            token = event.delta
            full_response += token
            placeholder.markdown(full_response)

    return full_response


# UI
st.set_page_config(page_title="pymentor", layout="centered")

st.title("🤖 PyMentor - Python Tutor ChatBot")
st.write("💡 Welcome To Your AI Powered Python Assistant")
st.caption("⚡ Streaming | 🔄 Resume Chat | 🎮 Controls Enabled | 💬 Multiple Chats")

st.sidebar.header("⚙️ Chat Settings")

# Session state
if "current_chat" not in st.session_state:
    st.session_state.current_chat = new_chat()

chat_files = list_chats()

# Select chat
selected_chat = st.sidebar.selectbox(
    "Select Chat",
    chat_files,
    index=chat_files.index(f"{st.session_state.current_chat}.json")
)

# Switch chat
if selected_chat.replace(".json", "") != st.session_state.current_chat:
    st.session_state.current_chat = selected_chat.replace(".json", "")
    st.rerun()

# New chat button
if st.sidebar.button("➕ New Chat"):
    st.session_state.current_chat = new_chat()
    st.rerun()

# Model + temperature
model = st.sidebar.selectbox("Choose Model", ["gpt-5.1", "gpt-4.1-mini"])
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

# Load messages
chat_path = os.path.join(CHAT_DIR, f"{st.session_state.current_chat}.json")
messages = load_chat(chat_path)

# Message count
message_count = len([m for m in messages if m["role"] != "system"])
st.sidebar.metric("💬 Messages", message_count)

# Show chat
for msg in messages:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).markdown(msg["content"])

# Input form
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Ask a Python Question",
        height=100,
        placeholder="For eg: Explain Python list with examples"
    )
    submit = st.form_submit_button("Ask PyMentor")

# Handle input
if submit and user_input.strip():
    st.chat_message("user").markdown(user_input)
    messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        typing = st.empty()
        typing.markdown("⏳ PyMentor is Typing...")
        time.sleep(0.5)

        placeholder = st.empty()

        ai_reply = stream_chat_with_ai(
            messages,
            placeholder,
            temperature,
            model
        )

        typing.write("")

    messages.append({"role": "assistant", "content": ai_reply})
    save_chat(chat_path, messages)
    st.rerun()

