"""Main Streamlit application for EchoVerse."""

import streamlit as st
import os
import time
from text_processor import get_text_processor
from tts_engine import get_tts_engine
from utils import (
    setup_directories,
    validate_text_input, 
    process_uploaded_file,
    clean_text_for_display,
    truncate_text,
    estimate_listening_time
)
from config import APP_TITLE, APP_SUBTITLE, AVAILABLE_TONES, AVAILABLE_VOICES, is_ibm_configured, is_huggingface_configured, AI_SERVICE


def check_environment_setup():
    """Check if required environment variables are set and provide guidance."""
    if AI_SERVICE == "ibm":
        watsonx_configured, tts_configured = is_ibm_configured()
        huggingface_configured = False
    else:
        watsonx_configured, tts_configured = False, False
        huggingface_configured = is_huggingface_configured()
    
    if (AI_SERVICE == "ibm" and (not watsonx_configured or not tts_configured)) or \
       (AI_SERVICE == "huggingface" and not huggingface_configured):
        
        st.sidebar.warning("⚠️ AI Services Not Fully Configured")
        
        with st.sidebar.expander("Setup Instructions"):
            st.write(f"""
            Currently using: **{AI_SERVICE.upper()}** service
            
            For full functionality, please set up your credentials:
            """)
            
            if AI_SERVICE == "ibm":
                st.write("""
                **IBM Watson Services:**
                1. **IBM Watsonx API Key**: Get from IBM Cloud console
                2. **IBM Watsonx Project ID**: Your project ID from Watsonx
                3. **IBM TTS API Key**: Get from IBM Text to Speech service
                """)
            else:
                st.write("""
                **Hugging Face Service:**
                1. **Hugging Face API Key**: Get from huggingface.co
                - Go to huggingface.co → your profile → Settings → Access Tokens
                - Create a new token and add it to your .env file
                """)
            
            st.write("""
            **Setup Options:**
            - Create a `.env` file in your project root
            - Set environment variables in your system
            - Use Streamlit secrets when deploying
            
            **Example .env file:**
            ```
            # For IBM Watson
            IBM_WATSONX_API_KEY=your_ibm_watsonx_key_here
            IBM_WATSONX_PROJECT_ID=your_ibm_project_id_here
            IBM_TTS_API_KEY=your_ibm_tts_key_here
            AI_SERVICE=ibm
            
            # For Hugging Face (alternative)
            HUGGINGFACE_API_KEY=your_huggingface_token_here
            AI_SERVICE=huggingface
            ```
            """)
            
            if AI_SERVICE == "ibm":
                if not watsonx_configured:
                    st.error("❌ IBM Watsonx not configured - AI text rewriting will use simulated responses")
                if not tts_configured:
                    st.error("❌ IBM TTS not configured - Using gTTS as fallback")
            else:
                if not huggingface_configured:
                    st.error("❌ Hugging Face not configured - AI text rewriting will use simulated responses")
    
    return True  # Always allow the app to run with fallbacks


def render_podcast_options():
    """Render podcast enhancement options."""
    st.subheader("🎙️ Podcast Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        podcast_mode = st.checkbox(
            "Podcast Mode", 
            value=True,
            help="Add professional podcast enhancements to your audio"
        )
    
    with col2:
        add_intro_outro = st.checkbox(
            "Intro/Outro Music", 
            value=True,
            disabled=not podcast_mode,
            help="Add intro and outro music to your podcast"
        )
    
    with col3:
        chapter_markers = st.checkbox(
            "Chapter Markers", 
            value=True,
            disabled=not podcast_mode,
            help="Add chapter markers for longer content"
        )
    
    if podcast_mode:
        st.info("🎧 Podcast mode will add professional audio enhancements, intro/outro music, and chapter markers.")
    
    return podcast_mode


def initialize_app():
    """Initialize the application with necessary setup."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Setup directories
    setup_directories()
    
    # Apply custom styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #4361ee;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6c757d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .tone-option {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #e9ecef;
        margin-bottom: 1rem;
        cursor: pointer;
    }
    .tone-option.selected {
        border-color: #4361ee;
        background-color: #f0f4ff;
    }
    .stat-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .podcast-badge {
        background-color: #8B5CF6;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .speaking-emoji {
        font-size: 3rem;
        text-align: center;
        margin: 1rem 0;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    .word-highlight {
        background-color: #4361ee;
        color: white;
        padding: 0.1rem 0.3rem;
        border-radius: 0.3rem;
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'original_text' not in st.session_state:
        st.session_state.original_text = ""
    if 'rewritten_text' not in st.session_state:
        st.session_state.rewritten_text = ""
    if 'audio_path' not in st.session_state:
        st.session_state.audio_path = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'selected_tone' not in st.session_state:
        st.session_state.selected_tone = "Neutral"
    if 'selected_voice' not in st.session_state:
        st.session_state.selected_voice = "Lisa"
    if 'podcast_mode' not in st.session_state:
        st.session_state.podcast_mode = False
    if 'is_playing' not in st.session_state:
        st.session_state.is_playing = False
    if 'current_word_index' not in st.session_state:
        st.session_state.current_word_index = 0


def render_header():
    """Render the application header."""
    st.markdown(f'<h1 class="main-header">🎵 {APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{APP_SUBTITLE}</p>', unsafe_allow_html=True)


def render_sidebar_info():
    """Render sidebar information."""
    with st.sidebar:
        st.header("ℹ️ About EchoVerse")
        st.write("EchoVerse transforms your text into expressive, downloadable audiobooks using AI technology.")
        
        st.header("🎯 How It Works")
        st.write("1. Paste text or upload a file")
        st.write("2. Choose your preferred tone")
        st.write("3. Select a voice profile")
        st.write("4. AI rewrites for expressiveness")
        st.write("5. Generate & download audio")
        
        st.header("🔧 Configuration")
        selected_tone = st.selectbox(
            "Select Tone",
            options=list(AVAILABLE_TONES.keys()),
            index=0,
            help="Choose the tone for your audiobook narration"
        )
        st.session_state.selected_tone = selected_tone
        st.info(AVAILABLE_TONES[selected_tone]["description"])
        
        selected_voice = st.selectbox(
            "Select Voice",
            options=list(AVAILABLE_VOICES.keys()),
            index=0,
            help="Choose the voice for your audiobook"
        )
        st.session_state.selected_voice = selected_voice
        st.info(AVAILABLE_VOICES[selected_voice]["description"])
        
        # Text statistics
        if st.session_state.original_text:
            st.header("📊 Text Statistics")
            words = len(st.session_state.original_text.split())
            chars = len(st.session_state.original_text)
            st.metric("Words", words)
            st.metric("Characters", chars)
            st.metric("Estimated Time", f"{round(words/200, 1)} min")


def handle_text_input():
    """Handle text input from user (paste or file upload)."""
    st.subheader("📄 Input Your Text")
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["✍️ Paste Text", "📁 Upload File"])
    
    text_content = ""
    
    with tab1:
        text_input = st.text_area(
            "Paste your text here:",
            height=200,
            placeholder="Enter the text you want to convert into an audiobook...",
            key="text_input"
        )
        if text_input:
            text_content = text_input
    
    with tab2:
        uploaded_file = st.file_uploader(
            "Choose a text file",
            type=['txt'],
            help="Upload a .txt file containing the text you want to convert"
        )
        
        if uploaded_file:
            success, content, error_msg = process_uploaded_file(uploaded_file)
            if success:
                text_content = content
                st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
                st.info(f"📊 Content preview: {truncate_text(content, 150)}")
            else:
                st.error(f"❌ {error_msg}")
    
    # Validate and store text
    if text_content:
        is_valid, error_msg = validate_text_input(text_content)
        if is_valid:
            st.session_state.original_text = clean_text_for_display(text_content)
            return True
        else:
            st.error(f"❌ {error_msg}")
            return False
    
    return bool(st.session_state.original_text)


def process_text_with_ai(text: str, tone: str):
    """
    Process text with AI rewriting.
    
    Args:
        text: Original text to process
        tone: Selected tone for rewriting
    """
    text_processor = get_text_processor()
    
    # Show processing status
    with st.spinner("🤖 Rewriting text with AI..."):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        
        rewritten_text = text_processor.rewrite_text(text, tone)
        
    if rewritten_text:
        st.session_state.rewritten_text = rewritten_text
        st.success("✅ Text successfully rewritten with AI!")
        return True
    else:
        st.error("❌ Failed to rewrite text. Please try again.")
        return False


def generate_audio(text: str, voice: str, tone: str, podcast_mode: bool = False):
    """
    Generate audio from text.
    
    Args:
        text: Text to convert to audio
        voice: Selected voice
        tone: Selected tone (for filename)
        podcast_mode: Whether to apply podcast enhancements
    """
    tts_engine = get_tts_engine()
    
    # Show processing status
    with st.spinner("🎵 Generating audio..."):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        
        result = tts_engine.generate_audio(text, voice, tone, podcast_mode=podcast_mode)
    
    if result['success']:
        st.session_state.audio_path = result['audio_path']
        st.session_state.audio_analysis = result['analysis']
        st.success("✅ Audio generated successfully!")
        return True
    else:
        st.error("❌ Failed to generate audio. Please try again.")
        return False


def render_text_comparison(original_text, rewritten_text, tone):
    """Render side-by-side text comparison."""
    st.subheader("📝 Text Comparison")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Text**")
        st.text_area("Original", value=original_text, height=300, key="original_display", label_visibility="collapsed")
    
    with col2:
        st.markdown(f"**Adapted Text ({tone})**")
        st.text_area("Rewritten", value=rewritten_text, height=300, key="rewritten_display", label_visibility="collapsed")


def render_speaking_emoji(is_playing=False):
    """Render animated speaking emoji."""
    emojis = ["🗣️", "🎤", "📢", "🔊", "📣"]
    
    if is_playing:
        # Animate through emojis
        emoji_index = int(time.time() * 2) % len(emojis)
        emoji = emojis[emoji_index]
        st.markdown(f'<div class="speaking-emoji">{emoji}</div>', unsafe_allow_html=True)
        st.caption("Speaking...")
    else:
        st.markdown(f'<div class="speaking-emoji">🎵</div>', unsafe_allow_html=True)
        st.caption("Ready to play")


def render_audio_player(audio_path, filename):
    """Render audio player and download button."""
    st.subheader("🎵 Audio Preview")
    
    # Show podcast badge if enhanced
    if st.session_state.get('podcast_mode', False):
        st.markdown('<div class="podcast-badge">🎙️ Podcast Enhanced</div>', unsafe_allow_html=True)
    
    # Read audio file
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    
    # Create columns for audio player and speaking emoji
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display audio player
        audio_placeholder = st.empty()
        audio_placeholder.audio(audio_bytes, format="audio/mp3")
    
    with col2:
        # Display speaking emoji
        render_speaking_emoji(st.session_state.get('is_playing', False))
    
    # Add JavaScript for audio playback detection
    st.markdown("""
    <script>
    function checkAudioPlayback() {
        const audioElement = document.querySelector('audio');
        if (audioElement) {
            audioElement.onplay = function() {
                window.parent.postMessage({type: 'audioPlay', data: true}, '*');
            };
            audioElement.onpause = function() {
                window.parent.postMessage({type: 'audioPlay', data: false}, '*');
            };
            audioElement.onended = function() {
                window.parent.postMessage({type: 'audioPlay', data: false}, '*');
            };
        }
    }
    
    // Check for audio element periodically
    setInterval(checkAudioPlayback, 1000);
    checkAudioPlayback();
    </script>
    """, unsafe_allow_html=True)
    
    # Handle messages from JavaScript
    try:
        # This is a simplified approach - in a real app you'd use more advanced techniques
        # to communicate between JS and Python in Streamlit
        if st.button("▶️ Play Audio"):
            st.session_state.is_playing = True
            st.rerun()
            
        if st.button("⏸️ Pause Audio"):
            st.session_state.is_playing = False
            st.rerun()
    except:
        pass
    
    # Show audio analysis if available
    if hasattr(st.session_state, 'audio_analysis'):
        analysis = st.session_state.audio_analysis
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words", analysis.get('word_count', 0))
        with col2:
            st.metric("Duration", f"{analysis.get('reading_time_minutes', 0)} min")
        with col3:
            st.metric("Enhanced", "Yes" if analysis.get('podcast_enhanced', False) else "No")
    
    # Download button
    st.download_button(
        label="📥 Download MP3",
        data=audio_bytes,
        file_name=filename,
        mime="audio/mpeg",
        use_container_width=True
    )


def main():
    """Main application function."""
    initialize_app()
    
    # Check environment setup
    check_environment_setup()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar_info()
    
    # Main content area
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Step 1: Text input
        has_text = handle_text_input()
        
        if has_text:
            # Show enhanced listening time estimate
            listening_time = estimate_listening_time(st.session_state.original_text)
            st.info(f"⏱️ Estimated listening time: {listening_time}")
            
            # Podcast options
            podcast_mode = render_podcast_options()
            
            st.markdown("---")
            
            # Step 2: Generate audiobook
            if st.button("🎵 Generate Audiobook", type="primary", use_container_width=True):
                # Process text with AI
                success = process_text_with_ai(st.session_state.original_text, st.session_state.selected_tone)
                
                if success:
                    # Generate audio
                    audio_success = generate_audio(
                        st.session_state.rewritten_text, 
                        st.session_state.selected_voice, 
                        st.session_state.selected_tone,
                        podcast_mode=podcast_mode
                    )
                    
                    if audio_success:
                        st.session_state.processing_complete = True
                        st.session_state.podcast_mode = podcast_mode
                        st.rerun()
    
    with col2:
        # Display processing results
        if st.session_state.rewritten_text and st.session_state.original_text:
            render_text_comparison(
                st.session_state.original_text,
                st.session_state.rewritten_text,
                st.session_state.selected_tone
            )
    
    # Display audio player if processing is complete
    if st.session_state.processing_complete and st.session_state.audio_path:
        st.markdown("---")
        filename = os.path.basename(st.session_state.audio_path)
        
        render_audio_player(st.session_state.audio_path, filename)
        
        # Add option to reset and start over
        if st.button("🔄 Create Another Audiobook", use_container_width=True):
            # Clear session state
            for key in ['original_text', 'rewritten_text', 'audio_path', 'processing_complete', 'podcast_mode', 'is_playing']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()