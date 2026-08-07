import streamlit as st
from api import send_message

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Banking Chatbot")

for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])


if question := st.chat_input("Nhập câu hỏi"):
    st.session_state.messages.append({"role": "user", "content": question})

    answer = send_message(question)
    st.session_state.messages.append({"role": "assistant", "content": answer})
