# main.py
"""Main Streamlit application for EchoVerse."""

import streamlit as st
import os
import time
from text_processor import get_text_processor
from tts_engine import get_tts_engine
from search_engine import get_search_engine
from podcast_narrator import get_podcast_narrator
from utils import (
    setup_directories,
    validate_text_input, 
    process_uploaded_file,
    clean_text_for_display,
    truncate_text,
    estimate_listening_time
)
from config import (
    APP_TITLE, APP_SUBTITLE, AVAILABLE_TONES, AVAILABLE_VOICES, 
    SUPPORTED_LANGUAGES, PODCAST_STYLES, get_voices_for_language,
    get_podcast_style_description, is_ibm_configured, is_huggingface_configured, AI_SERVICE
)


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
    
    return True


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
    .section-header {
        font-size: 1.5rem;
        color: #4361ee;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e9ecef;
        padding-bottom: 0.5rem;
    }
    .config-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
        margin-bottom: 1.5rem;
    }
    .stat-box {
        background-color: #f0f4ff;
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
        st.session_state.selected_voice = "Alexa"
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = "Telugu"
    if 'podcast_mode' not in st.session_state:
        st.session_state.podcast_mode = False
    if 'podcast_narrator_mode' not in st.session_state:
        st.session_state.podcast_narrator_mode = False
    if 'podcast_topic' not in st.session_state:
        st.session_state.podcast_topic = ""
    if 'podcast_style' not in st.session_state:
        st.session_state.podcast_style = "Educational"
    if 'show_search' not in st.session_state:
        st.session_state.show_search = False


def render_header():
    """Render the application header."""
    st.markdown(f'<h1 class="main-header">{APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{APP_SUBTITLE}</p>', unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with configuration options."""
    with st.sidebar:
        st.markdown("### About EchoVerse")
        st.write("EchoVerse transforms your text into expressive, downloadable audiobooks using AI technology.")
        
        st.markdown("### How It Works")
        st.write("1. Paste text or upload a file")
        st.write("2. Choose your preferred tone")
        st.write("3. Select a voice profile")
        st.write("4. AI rewrites for expressiveness")
        st.write("5. Generate & download audio")
        
        st.markdown("---")
        st.markdown("### Configuration")
        
        # Language selection
        selected_language = st.selectbox(
            "Select Language",
            options=list(SUPPORTED_LANGUAGES.keys()),
            index=list(SUPPORTED_LANGUAGES.keys()).index("Telugu") if "Telugu" in SUPPORTED_LANGUAGES else 0,
            help="Choose the language for your audiobook"
        )
        st.session_state.selected_language = selected_language
        
        # Get available voices for the selected language
        language_voices = get_voices_for_language(selected_language)
        
        selected_voice = st.selectbox(
            "Select Voice",
            options=list(language_voices.keys()),
            index=0,
            help="Choose the voice for your audiobook"
        )
        st.session_state.selected_voice = selected_voice
        
        # Show voice description
        voice_info = language_voices.get(selected_voice, {})
        if voice_info:
            st.info(voice_info.get("description", "No description available"))
        
        selected_tone = st.selectbox(
            "Select Tone",
            options=list(AVAILABLE_TONES.keys()),
            index=0,
            help="Choose the tone for your audiobook narration"
        )
        st.session_state.selected_tone = selected_tone
        st.info(AVAILABLE_TONES[selected_tone]["description"])
        
        # Text statistics
        if st.session_state.original_text:
            st.markdown("### Text Statistics")
            words = len(st.session_state.original_text.split())
            chars = len(st.session_state.original_text)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Words", words)
            with col2:
                st.metric("Characters", chars)
            st.metric("Estimated Time", f"{round(words/200, 1)} min")


def render_text_input():
    """Render text input section."""
    st.markdown('<div class="section-header">Input Your Text</div>', unsafe_allow_html=True)
    
    # Example text button
    if st.button("📋 Load Example Text", use_container_width=True):
        st.session_state.original_text = """Artificial intelligence is transforming the way we live and work. From healthcare to education, AI systems are helping humans solve complex problems and make better decisions. 

The potential of AI is enormous, but it also comes with important ethical considerations that we must address as a society. As we continue to develop these technologies, we must ensure they are used responsibly and for the benefit of all humanity.

The future of AI is not just about technological advancement, but about creating systems that understand human values and work in harmony with people."""
    
    # Text input area
    text_input = st.text_area(
        "Enter your text here:",
        height=200,
        value=st.session_state.original_text,
        placeholder="Type or paste your text here...",
        help="Enter the text you want to convert to an audiobook",
        key="text_input"
    )
    
    if text_input != st.session_state.original_text:
        st.session_state.original_text = text_input
        st.session_state.processing_complete = False
    
    # File upload option
    uploaded_file = st.file_uploader(
        "Or upload a text file",
        type=['txt'],
        help="Upload a .txt file containing your text"
    )
    
    if uploaded_file is not None:
        success, content, error_msg = process_uploaded_file(uploaded_file)
        if success:
            st.session_state.original_text = content
            st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
        else:
            st.error(f"❌ {error_msg}")


def render_podcast_narrator():
    """Render podcast narrator section."""
    st.markdown('<div class="section-header">AI Podcast Narrator</div>', unsafe_allow_html=True)
    
    # Podcast narrator mode toggle
    podcast_narrator_mode = st.checkbox(
        "Enable Podcast Narrator Mode",
        value=st.session_state.podcast_narrator_mode,
        help="Transform your content into a professional podcast format"
    )
    
    if podcast_narrator_mode != st.session_state.podcast_narrator_mode:
        st.session_state.podcast_narrator_mode = podcast_narrator_mode
        st.session_state.processing_complete = False
    
    if podcast_narrator_mode:
        # Podcast topic
        podcast_topic = st.text_input(
            "Podcast Topic (optional)",
            value=st.session_state.podcast_topic,
            placeholder="e.g., The Future of AI, Climate Change Explained",
            help="Provide a topic to help the AI create a better podcast script"
        )
        st.session_state.podcast_topic = podcast_topic
        
        # Podcast style
        podcast_style = st.selectbox(
            "Podcast Style",
            options=list(PODCAST_STYLES.keys()),
            index=list(PODCAST_STYLES.keys()).index("Educational") if "Educational" in PODCAST_STYLES else 0,
            help="Choose the style for your podcast"
        )
        st.session_state.podcast_style = podcast_style
        st.info(get_podcast_style_description(podcast_style))
        
        st.info("🎧 The AI will transform your content into a podcast script with intro, structured explanation, and outro.")


def render_processing_options():
    """Render processing options section."""
    st.markdown('<div class="section-header">Processing Options</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_shorten = st.checkbox(
            "Auto-Shorten Long Text",
            value=True,
            help="Automatically shorten very long text for better audio quality"
        )
    
    with col2:
        enhance_audio = st.checkbox(
            "Audio Enhancements",
            value=True,
            help="Apply audio processing for better sound quality"
        )
    
    podcast_mode = st.checkbox(
        "Podcast Mode",
        value=st.session_state.podcast_mode,
        help="Add podcast-style enhancements to the audio"
    )
    
    if podcast_mode != st.session_state.podcast_mode:
        st.session_state.podcast_mode = podcast_mode
        st.session_state.processing_complete = False
    
    # Generate button
    if st.button("🎵 Generate Audiobook", type="primary", use_container_width=True):
        if not st.session_state.original_text.strip():
            st.error("Please enter some text to convert.")
            return
        
        with st.spinner("Processing your audiobook..."):
            try:
                # Process text with AI
                processor = get_text_processor()
                
                # Use podcast narrator if enabled
                if st.session_state.podcast_narrator_mode:
                    podcast_narrator = get_podcast_narrator()
                    podcast_script = podcast_narrator.generate_podcast_script(
                        st.session_state.original_text,
                        st.session_state.podcast_topic,
                        st.session_state.podcast_style
                    )
                    st.session_state.rewritten_text = podcast_script
                else:
                    # Standard text processing
                    result = processor.process_text(
                        st.session_state.original_text,
                        st.session_state.selected_tone,
                        st.session_state.selected_language,
                        auto_shorten
                    )
                    st.session_state.rewritten_text = result['rewritten_text']
                
                # Generate audio
                tts_engine = get_tts_engine()
                audio_result = tts_engine.generate_audio(
                    st.session_state.rewritten_text,
                    st.session_state.selected_voice,
                    st.session_state.selected_tone,
                    st.session_state.selected_language,
                    auto_shorten,
                    podcast_mode
                )
                
                if audio_result['success']:
                    st.session_state.audio_path = audio_result['audio_path']
                    st.session_state.processing_complete = True
                    st.session_state.analysis = audio_result['analysis']
                    st.rerun()
                else:
                    st.error(f"Audio generation failed: {audio_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


def render_results():
    """Render the results section."""
    if not st.session_state.processing_complete:
        return
    
    st.markdown('<div class="section-header">Your Audiobook is Ready!</div>', unsafe_allow_html=True)
    
    # Display analysis results
    if hasattr(st.session_state, 'analysis'):
        analysis = st.session_state.analysis
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Words", analysis['word_count'])
        
        with col2:
            st.metric("Duration", f"{analysis['reading_time_minutes']} min")
        
        with col3:
            st.metric("Format", "Podcast" if analysis.get('podcast_enhanced', False) else "Standard")
    
    # Audio player
    if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
        st.audio(st.session_state.audio_path, format="audio/mp3")
        
        # Download button
        with open(st.session_state.audio_path, "rb") as f:
            audio_bytes = f.read()
        
        st.download_button(
            label="⬇️ Download Audiobook",
            data=audio_bytes,
            file_name=os.path.basename(st.session_state.audio_path),
            mime="audio/mp3",
            use_container_width=True
        )
    
    # Display processed text
    if st.session_state.rewritten_text:
        with st.expander("View Processed Text"):
            st.write(st.session_state.rewritten_text)


def main():
    """Main application function."""
    # Initialize the app
    initialize_app()
    
    # Check environment setup
    check_environment_setup()
    
    # Render the header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    render_text_input()
    render_podcast_narrator()
    render_processing_options()
    render_results()


if __name__ == "__main__":
    main()