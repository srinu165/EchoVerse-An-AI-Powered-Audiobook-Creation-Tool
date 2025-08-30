# config.py
"""Configuration settings for EchoVerse application."""

import os
import streamlit as st
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application settings
APP_TITLE = "EchoVerse"
APP_SUBTITLE = "Transforms your text into expressive, downloadable audiobooks using AI technology"
MAX_TEXT_LENGTH = 10000
SUPPORTED_FILE_TYPES = ['.txt']

# Language settings
SUPPORTED_LANGUAGES = {
    "English": {"code": "en", "name": "English"},
    "Hindi": {"code": "hi", "name": "Hindi"},
    "Telugu": {"code": "te", "name": "Telugu"},
    "Spanish": {"code": "es", "name": "Spanish"},
    "French": {"code": "fr", "name": "French"},
    "German": {"code": "de", "name": "German"},
    "Italian": {"code": "it", "name": "Italian"},
    "Portuguese": {"code": "pt", "name": "Portuguese"},
    "Japanese": {"code": "ja", "name": "Japanese"},
    "Korean": {"code": "ko", "name": "Korean"},
    "Chinese": {"code": "zh", "name": "Chinese"},
    "Arabic": {"code": "ar", "name": "Arabic"},
    "Russian": {"code": "ru", "name": "Russian"}
}

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

# Voice settings - updated with Alexa and Mazeo voices for Telugu
AVAILABLE_VOICES = {
    "English": {
        "Lisa": {
            "description": "Female voice, warm and professional",
            "voice": "en-US_LisaV3Voice",
            "gtts_voice": None
        },
        "Michael": {
            "description": "Male voice, clear and authoritative", 
            "voice": "en-US_MichaelV3Voice",
            "gtts_voice": None
        },
        "Allison": {
            "description": "Female voice, friendly and engaging",
            "voice": "en-US_AllisonV3Voice",
            "gtts_voice": None
        }
    },
    "Telugu": {
        "Alexa": {
            "description": "Female Telugu voice, clear and expressive",
            "voice": "te-IN_NeerjaV3Voice",  # Using Neerja as Alexa equivalent
            "gtts_voice": "te"
        },
        "Mazeo": {
            "description": "Male Telugu voice, deep and authoritative",
            "voice": "te-IN_MohanV3Voice",  # Using Mohan as Mazeo equivalent
            "gtts_voice": "te"
        },
        "Default": {
            "description": "Standard Telugu voice",
            "voice": "te-IN_MohanV3Voice",
            "gtts_voice": "te"
        }
    },
    "Hindi": {
        "Default": {
            "description": "Standard Hindi voice",
            "voice": "hi-IN_KaranV3Voice",
            "gtts_voice": "hi"
        }
    },
    "Spanish": {
        "Default": {
            "description": "Standard Spanish voice",
            "voice": "es-ES_LauraV3Voice",
            "gtts_voice": "es"
        }
    }
}

# Podcast styles
PODCAST_STYLES = {
    "Conversational": "Friendly, chatty style like a casual conversation",
    "Educational": "Informative, explanatory style for learning content",
    "Storytelling": "Narrative style with dramatic elements",
    "News": "Formal, authoritative style like news reporting",
    "Interview": "Question-answer format with multiple voices"
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
    "Inspiring": "microsoft/DialoGPT-large"
}

# Podcast settings
PODCAST_SETTINGS = {
    "intro_music": os.path.join(ASSETS_DIR, "intro_music.mp3"),
    "outro_music": os.path.join(ASSETS_DIR, "outro_music.mp3"),
    "chapter_pause_duration": 1.5,
    "intro_fade_duration": 3.0,
    "default_host": "EchoVerse AI Narrator"
}

# Audio enhancement settings
AUDIO_ENHANCEMENTS = {
    "noise_reduction": True,
    "volume_normalization": True,
    "eq_preset": "podcast",
    "compression": True
}

# Chapter markers
CHAPTER_SETTINGS = {
    "max_chapter_length": 600,
    "chapter_announcements": True,
    "chapter_fade": True
}


def is_ibm_configured():
    """Check if IBM Watson services are properly configured."""
    watsonx_configured = bool(IBM_WATSONX_API_KEY and IBM_WATSONX_PROJECT_ID)
    tts_configured = bool(IBM_TTS_API_KEY)
    return watsonx_configured, tts_configured

def is_huggingface_configured():
    """Check if Hugging Face is properly configured."""
    return bool(HUGGINGFACE_API_KEY)

def get_voices_for_language(language):
    """Get available voices for a specific language."""
    return AVAILABLE_VOICES.get(language, AVAILABLE_VOICES["English"])

def get_podcast_style_description(style):
    """Get description for a podcast style."""
    return PODCAST_STYLES.get(style, "Standard podcast style")