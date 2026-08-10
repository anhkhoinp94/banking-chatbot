import streamlit as st
from api import send_message

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Banking Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


if question := st.chat_input("Nhập câu hỏi"):
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.write("Đang chờ trả lời...")
        answer = send_message(question)
        placeholder.write(answer)

    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append({"role": "assistant", "content": answer})
