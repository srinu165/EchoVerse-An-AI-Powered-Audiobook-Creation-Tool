import streamlit as st
import time

def speaking_emoji(is_speaking=False):
    """Display an animated speaking emoji."""
    if is_speaking:
        # Create a placeholder for the emoji
        emoji_placeholder = st.empty()
        
        # Animate the emoji
        emojis = ["🗣️", "🎤", "📢", "🔊", "📣"]
        while st.session_state.get('is_playing', False):
            for emoji in emojis:
                if not st.session_state.get('is_playing', False):
                    break
                emoji_placeholder.markdown(f'<div style="font-size: 3rem; text-align: center;">{emoji}</div>', unsafe_allow_html=True)
                time.sleep(0.3)
        
        # Clear the placeholder when done
        emoji_placeholder.empty()
    else:
        st.markdown('<div style="font-size: 3rem; text-align: center;">🎵</div>', unsafe_allow_html=True)