import streamlit as st

def update_player_id():
    if st.session_state.detected_ids:
        st.session_state.input_id = st.session_state.detected_ids

def clear_id():
    st.session_state.input_id = ""
    st.session_state.detected_ids = None

def update_card_mode(key: str, new_mode: str):
    st.session_state[key] = new_mode