"""Utility functions for EchoVerse application."""

import os
import tempfile
import streamlit as st
from typing import Optional, Tuple
from config import TEMP_DIR, AUDIO_DIR, MAX_TEXT_LENGTH, SUPPORTED_FILE_TYPES
from config import PODCAST_SETTINGS, AUDIO_ENHANCEMENTS, CHAPTER_SETTINGS, ASSETS_DIR


def setup_directories():
    """Create necessary directories for temporary files."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)


def validate_text_input(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate input text for processing.
    
    Args:
        text: Input text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Please provide some text to process."
    
    if len(text) > MAX_TEXT_LENGTH:
        return False, f"Text is too long. Maximum length is {MAX_TEXT_LENGTH} characters."
    
    return True, None


def process_uploaded_file(uploaded_file) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Process uploaded text file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (success, content, error_message)
    """
    if uploaded_file is None:
        return False, None, "No file uploaded."
    
    # Check file extension
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    if file_extension not in SUPPORTED_FILE_TYPES:
        return False, None, f"Unsupported file type. Please upload a .txt file."
    
    try:
        # Read file content
        content = uploaded_file.getvalue().decode('utf-8')
        
        # Validate content
        is_valid, error_msg = validate_text_input(content)
        if not is_valid:
            return False, None, error_msg
            
        return True, content, None
        
    except UnicodeDecodeError:
        return False, None, "Unable to read file. Please ensure it's a valid text file."
    except Exception as e:
        return False, None, f"Error processing file: {str(e)}"


def clean_text_for_display(text: str) -> str:
    """
    Clean text for display in the interface.
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text suitable for display
    """
    # Remove excessive whitespace while preserving paragraph structure
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = ' '.join(line.split())
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    
    return '\n\n'.join(cleaned_lines)


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text for preview purposes.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def generate_filename(base_name: str, tone: str, voice: str, extension: str = ".mp3") -> str:
    """
    Generate a descriptive filename for audio output.
    
    Args:
        base_name: Base filename or title
        tone: Selected tone
        voice: Selected voice
        extension: File extension
        
    Returns:
        Generated filename
    """
    # Clean base name for filename
    clean_base = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
    clean_base = clean_base.replace(' ', '_')
    
    if not clean_base:
        clean_base = "audiobook"
    
    return f"{clean_base}_{tone.lower()}_{voice.lower()}{extension}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def create_podcast_audio(audio_path, text, tone, voice):
    """
    Enhance audio with podcast-style features.
    """
    try:
        # Import audio processing libraries
        from pydub import AudioSegment, effects
        from pydub.generators import WhiteNoise
        import os
        
        # Load original audio
        original_audio = AudioSegment.from_mp3(audio_path)
        
        # Apply audio enhancements
        enhanced_audio = apply_audio_enhancements(original_audio)
        
        # Add intro/outro music
        podcast_audio = add_music_intro_outro(enhanced_audio)
        
        # Add chapter markers if content is long
        if len(enhanced_audio) > CHAPTER_SETTINGS["max_chapter_length"] * 1000:
            podcast_audio = add_chapter_markers(podcast_audio, text)
        
        # Generate new filename
        podcast_filename = generate_filename("podcast", tone, voice, "_podcast.mp3")
        podcast_path = os.path.join(AUDIO_DIR, podcast_filename)
        
        # Export final podcast audio
        podcast_audio.export(podcast_path, format="mp3", bitrate="192k")
        
        return podcast_path
        
    except Exception as e:
        print(f"Error creating podcast audio: {e}")
        return audio_path  # Fallback to original audio


def apply_audio_enhancements(audio_segment):
    """
    Apply professional audio enhancements.
    """
    from pydub import effects, AudioSegment
    
    # Noise reduction (simple approach)
    if AUDIO_ENHANCEMENTS["noise_reduction"]:
        try:
            # Simple noise gate implementation
            audio_segment = effects.normalize(audio_segment)
        except:
            pass
    
    # Volume normalization
    if AUDIO_ENHANCEMENTS["volume_normalization"]:
        audio_segment = effects.normalize(audio_segment)
    
    # EQ adjustments based on preset
    if AUDIO_ENHANCEMENTS["eq_preset"] == "podcast":
        # Boost mid frequencies for voice clarity
        audio_segment = audio_segment.low_pass_filter(8000).high_pass_filter(80)
    
    # Compression for consistent volume
    if AUDIO_ENHANCEMENTS["compression"]:
        try:
            audio_segment = effects.compress_dynamic_range(audio_segment)
        except:
            pass
    
    return audio_segment


def add_music_intro_outro(audio_segment):
    """
    Add intro and outro music to audio.
    """
    from pydub import AudioSegment
    
    try:
        # Try to load intro music
        intro_music = AudioSegment.silent(duration=3000)  # Default silent intro
        
        # Add intro music with fade in
        final_audio = intro_music.append(audio_segment, crossfade=1500)
        
        # Add outro music with fade out
        outro_music = AudioSegment.silent(duration=2000)  # Default silent outro
        final_audio = final_audio.append(outro_music, crossfade=1500)
        
        return final_audio
        
    except Exception as e:
        print(f"Error adding music: {e}")
        return audio_segment  # Return original if music fails


def add_chapter_markers(audio_segment, text):
    """
    Add chapter markers for long content.
    """
    from pydub import AudioSegment
    from pydub.generators import Sine
    
    try:
        # Simple chapter marker (beep sound)
        chapter_marker = Sine(1000).to_audio_segment(duration=300).apply_gain(-20)
        silence = AudioSegment.silent(duration=500)
        
        # For demonstration, add a marker every 5 minutes
        segment_length = len(audio_segment)
        chapter_interval = 5 * 60 * 1000  # 5 minutes in milliseconds
        
        if segment_length > chapter_interval:
            final_audio = AudioSegment.empty()
            position = 0
            
            while position < segment_length:
                chunk = audio_segment[position:position + chapter_interval]
                final_audio += chunk
                final_audio += silence + chapter_marker + silence
                position += chapter_interval
            
            return final_audio
            
    except Exception as e:
        print(f"Error adding chapter markers: {e}")
    
    return audio_segment


def estimate_listening_time(text):
    """
    Estimate listening time with enhancements.
    """
    words = len(text.split())
    base_time = words / 150  # 150 words per minute
    
    # Add time for podcast features
    enhanced_time = base_time + 0.5  # Add 30 seconds for intro/outro
    
    minutes = int(enhanced_time)
    seconds = int((enhanced_time - minutes) * 60)
    
    return f"{minutes} min {seconds} sec"


def highlight_spoken_words(text, current_word_index):
    """
    Highlight words in text as they are being spoken.
    
    Args:
        text: The text to highlight
        current_word_index: Index of the current word being spoken
        
    Returns:
        HTML with highlighted words
    """
    words = text.split()
    highlighted_text = []
    
    for i, word in enumerate(words):
        if i == current_word_index:
            highlighted_text.append(f'<span class="word-highlight">{word}</span>')
        else:
            highlighted_text.append(word)
    
    return ' '.join(highlighted_text)