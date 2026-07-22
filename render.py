import streamlit as st
from streamlit_widgets import update_card_mode

def sp_mp_toggle(key: str) -> str:
    """Render the Singleplayer/Multiplayer toggle buttons and return the active mode."""
    col_sp, col_mp = st.columns(2)
    mode = st.session_state.get(key, "SP")
    with col_sp:
        st.button(
            "⚔️ Singleplayer",
            use_container_width=True,
            type="primary" if mode == "SP" else "secondary",
            on_click=update_card_mode,
            args=(key, "SP"),
        )
    with col_mp:
        st.button(
            "👥 Multiplayer",
            use_container_width=True,
            type="primary" if mode == "MP" else "secondary",
            on_click=update_card_mode,
            args=(key, "MP"),
        )
    return st.session_state.get(key, "SP")
