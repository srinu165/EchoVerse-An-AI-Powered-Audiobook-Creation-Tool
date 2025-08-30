"""Configuration settings for EchoVerse application."""

import os
import streamlit as st
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application settings
APP_TITLE = "EchoVerse"
APP_SUBTITLE = "An AI-Powered Audiobook Creation Tool"
MAX_TEXT_LENGTH = 10000
SUPPORTED_FILE_TYPES = ['.txt']

# Tone settings
AVAILABLE_TONES = {
    "Neutral": {
        "description": "Clear, balanced narration suitable for educational content",
        "color": "#3B82F6",
        "prompt": "Rewrite the following text in a neutral, clear, and educational tone while maintaining all key information and meaning: "
    },
    "Suspenseful": {
        "description": "Dramatic, engaging style perfect for thrillers and mysteries", 
        "color": "#8B5CF6",
        "prompt": "Rewrite the following text with a suspenseful, dramatic tone that builds tension and engages the reader while preserving the original meaning: "
    },
    "Inspiring": {
        "description": "Uplifting, motivational delivery for personal development",
        "color": "#10B981", 
        "prompt": "Rewrite the following text with a inspiring, motivational tone that uplifts and encourages while maintaining the original message: "
    }
}

# Voice settings
AVAILABLE_VOICES = {
    "Lisa": {
        "description": "Female voice, warm and professional",
        "voice": "en-US_LisaV3Voice"
    },
    "Michael": {
        "description": "Male voice, clear and authoritative", 
        "voice": "en-US_MichaelV3Voice"
    },
    "Allison": {
        "description": "Female voice, friendly and engaging",
        "voice": "en-US_AllisonV3Voice"
    }
}

# Try to load from Streamlit secrets, fallback to environment variables
try:
    # IBM Watson Configuration
    IBM_WATSONX_API_KEY = st.secrets.get("IBM_WATSONX_API_KEY", os.getenv("IBM_WATSONX_API_KEY", ""))
    IBM_WATSONX_API_URL = st.secrets.get("IBM_WATSONX_API_URL", os.getenv("IBM_WATSONX_API_URL", "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation"))
    IBM_WATSONX_PROJECT_ID = st.secrets.get("IBM_WATSONX_PROJECT_ID", os.getenv("IBM_WATSONX_PROJECT_ID", ""))
    
    # IBM Watson Text to Speech Configuration
    IBM_TTS_API_KEY = st.secrets.get("IBM_TTS_API_KEY", os.getenv("IBM_TTS_API_KEY", ""))
    IBM_TTS_URL = st.secrets.get("IBM_TTS_URL", os.getenv("IBM_TTS_URL", "https://api.us-south.text-to-speech.watson.cloud.ibm.com"))
    
    # Hugging Face Configuration
    HUGGINGFACE_API_KEY = st.secrets.get("HUGGINGFACE_API_KEY", os.getenv("HUGGINGFACE_API_KEY", ""))
    HUGGINGFACE_API_URL = st.secrets.get("HUGGINGFACE_API_URL", os.getenv("HUGGINGFACE_API_URL", "https://api-inference.huggingface.co/models"))
except:
    # Fallback to environment variables only
    IBM_WATSONX_API_KEY = os.getenv("IBM_WATSONX_API_KEY", "")
    IBM_WATSONX_API_URL = os.getenv("IBM_WATSONX_API_URL", "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation")
    IBM_WATSONX_PROJECT_ID = os.getenv("IBM_WATSONX_PROJECT_ID", "")
    IBM_TTS_API_KEY = os.getenv("IBM_TTS_API_KEY", "")
    IBM_TTS_URL = os.getenv("IBM_TTS_URL", "https://api.us-south.text-to-speech.watson.cloud.ibm.com")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_API_URL = os.getenv("HUGGINGFACE_API_URL", "https://api-inference.huggingface.co/models")

# File paths
TEMP_DIR = "temp"
AUDIO_DIR = os.path.join(TEMP_DIR, "audio")
ASSETS_DIR = "assets"

# AI Service selection
AI_SERVICE = os.getenv("AI_SERVICE", "huggingface")  # huggingface or ibm

# Hugging Face Models for different tones
HUGGINGFACE_MODELS = {
    "Neutral": "microsoft/DialoGPT-medium",
    "Suspenseful": "gpt2",
    "Inspiring": "microsoft/DialoGPT-large",
    "Podcast": "microsoft/DialoGPT-large"  # Added podcast model
}

# Podcast settings
PODCAST_SETTINGS = {
    "intro_music": os.path.join(ASSETS_DIR, "intro_music.mp3"),  # Path to intro music file
    "outro_music": os.path.join(ASSETS_DIR, "outro_music.mp3"),  # Path to outro music file
    "chapter_pause_duration": 1.5,  # seconds pause between chapters
    "intro_fade_duration": 3.0,  # seconds for music fade in/out
    "default_host": "EchoVerse AI Narrator"
}

# Audio enhancement settings
AUDIO_ENHANCEMENTS = {
    "noise_reduction": True,
    "volume_normalization": True,
    "eq_preset": "podcast",  # podcast, audiobook, voice, flat
    "compression": True
}

# Chapter markers (for longer content)
CHAPTER_SETTINGS = {
    "max_chapter_length": 600,  # seconds (10 minutes)
    "chapter_announcements": True,
    "chapter_fade": True
}


# Add a function to check if services are configured
def is_ibm_configured():
    """Check if IBM Watson services are properly configured."""
    watsonx_configured = bool(IBM_WATSONX_API_KEY and IBM_WATSONX_PROJECT_ID)
    tts_configured = bool(IBM_TTS_API_KEY)
    return watsonx_configured, tts_configured

def is_huggingface_configured():
    """Check if Hugging Face is properly configured."""
    return bool(HUGGINGFACE_API_KEY)