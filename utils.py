# utils.py
"""Utility functions for EchoVerse application."""

import os
import re
import uuid
import streamlit as st
from typing import Optional
from config import TEMP_DIR, AUDIO_DIR, ASSETS_DIR, SUPPORTED_FILE_TYPES, MAX_TEXT_LENGTH


def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)


def validate_text_input(text: str) -> tuple:
    """
    Validate text input for length and content.
    
    Args:
        text: Input text to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text.strip():
        return False, "Please enter some text to convert."
    
    if len(text) > MAX_TEXT_LENGTH:
        return False, f"Text is too long. Maximum {MAX_TEXT_LENGTH} characters allowed."
    
    # Check if text contains mostly non-alphanumeric characters
    alphanumeric_chars = len(re.findall(r'[a-zA-Z0-9]', text))
    if alphanumeric_chars < len(text) * 0.1:  # Less than 10% alphanumeric
        return False, "Text doesn't contain enough readable content."
    
    return True, ""


def process_uploaded_file(uploaded_file) -> Optional[str]:
    """
    Process uploaded file and extract text content.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Extracted text or None if failed
    """
    try:
        if uploaded_file.type == "text/plain":
            text = uploaded_file.getvalue().decode("utf-8")
            
            # Validate the extracted text
            is_valid, error_msg = validate_text_input(text)
            if not is_valid:
                st.error(error_msg)
                return None
                
            return text
        else:
            st.error(f"Unsupported file type. Please upload a text file (.txt).")
            return None
            
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None


def generate_filename(prefix: str, tone: str, voice: str, extension: str = ".mp3") -> str:
    """
    Generate a unique filename for audio files.
    
    Args:
        prefix: File prefix (e.g., "audiobook")
        tone: Selected tone
        voice: Selected voice
        extension: File extension
        
    Returns:
        Generated filename
    """
    timestamp = int(time.time())
    short_id = str(uuid.uuid4())[:8]
    safe_tone = re.sub(r'[^a-zA-Z0-9]', '', tone)
    safe_voice = re.sub(r'[^a-zA-Z0-9]', '', voice)
    
    return f"{prefix}_{safe_tone}_{safe_voice}_{timestamp}_{short_id}{extension}"


def clean_text_for_display(text: str, max_length: int = 1000) -> str:
    """
    Clean and format text for display in the UI.
    
    Args:
        text: Text to clean
        max_length: Maximum length to display
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Ensure proper sentence spacing
    text = re.sub(r'\.([a-zA-Z])', r'. \1', text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text


def truncate_text(text: str, max_words: int = 100) -> str:
    """
    Truncate text to a maximum number of words.
    
    Args:
        text: Text to truncate
        max_words: Maximum number of words
        
    Returns:
        Truncated text
    """
    words = text.split()
    if len(words) <= max_words:
        return text
    
    return ' '.join(words[:max_words]) + '...'


def estimate_listening_time(word_count: int, words_per_minute: int = 150) -> float:
    """
    Estimate listening time based on word count.
    
    Args:
        word_count: Number of words
        words_per_minute: Average reading speed
        
    Returns:
        Estimated time in minutes
    """
    return round(word_count / words_per_minute, 1)


def format_time(seconds: int) -> str:
    """
    Format seconds into MM:SS format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename


def get_file_size(filepath: str) -> str:
    """
    Get human-readable file size.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Human-readable file size string
    """
    try:
        size_bytes = os.path.getsize(filepath)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    except:
        return "Unknown"


def create_podcast_audio(audio_path: str, text: str, tone: str, voice: str) -> str:
    """
    Create enhanced podcast audio with intro/outro music.
    
    Args:
        audio_path: Path to the main audio file
        text: The text content
        tone: Selected tone
        voice: Selected voice
        
    Returns:
        Path to the enhanced podcast audio file
    """
    # This is a placeholder function - in a real implementation, you would use
    # a library like pydub to mix audio files with intro/outro music
    
    # For now, just return the original path
    return audio_path


def is_audio_file(filepath: str) -> bool:
    """
    Check if a file is an audio file based on extension.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if it's an audio file, False otherwise
    """
    audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
    return os.path.splitext(filepath)[1].lower() in audio_extensions


def get_available_audio_files() -> list:
    """
    Get list of available audio files in the audio directory.
    
    Returns:
        List of audio file paths
    """
    if not os.path.exists(AUDIO_DIR):
        return []
    
    audio_files = []
    for filename in os.listdir(AUDIO_DIR):
        if is_audio_file(filename):
            audio_files.append(os.path.join(AUDIO_DIR, filename))
    
    return sorted(audio_files, key=os.path.getmtime, reverse=True)