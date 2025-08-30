# tts_engine.py
"""Text-to-Speech engine for audio generation with text analysis and summarization."""

import os
import streamlit as st
import time  # Added missing import
from typing import Optional, Dict, Any
from config import AVAILABLE_VOICES, AUDIO_DIR, SUPPORTED_LANGUAGES
from utils import generate_filename
from gtts import gTTS
import re
from collections import Counter
from search_engine import get_search_engine

# Try to import IBM Watson TTS if configured
try:
    from ibm_watson import TextToSpeechV1
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
    from config import IBM_TTS_API_KEY, IBM_TTS_URL
    IBM_TTS_AVAILABLE = bool(IBM_TTS_API_KEY)
except ImportError:
    IBM_TTS_AVAILABLE = False

# Try to import NLTK with fallback
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.corpus import stopwords
    
    # Download required NLTK data with error handling
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            print("NLTK punkt download failed, using fallback tokenizer")
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            print("NLTK stopwords download failed, using fallback stopwords")
    
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("NLTK not available, using fallback text processing methods")


class TextAnalyzer:
    """Handles text analysis and summarization."""
    
    def __init__(self):
        self.stop_words = self._get_stopwords()
    
    def _get_stopwords(self):
        """Get stopwords with fallback if NLTK is not available."""
        if NLTK_AVAILABLE:
            try:
                return set(stopwords.words('english'))
            except:
                pass
        
        # Fallback basic English stopwords
        return {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 
            'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 
            'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 
            'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 
            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 
            'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 
            'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
            'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 
            'will', 'just', 'should', 'now'
        }
    
    def _simple_sent_tokenize(self, text: str) -> list:
        """Simple sentence tokenizer fallback."""
        # Split on common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out empty strings
        return [s.strip() for s in sentences if s.strip()]
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze the input text and provide statistics.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Basic statistics
        char_count = len(text)
        words = text.split()
        word_count = len(words)
        
        # Sentence count with fallback
        if NLTK_AVAILABLE:
            try:
                sentence_count = len(sent_tokenize(text))
            except:
                sentence_count = len(self._simple_sent_tokenize(text))
        else:
            sentence_count = len(self._simple_sent_tokenize(text))
        
        # Word frequency analysis
        words_lower = re.findall(r'\b\w+\b', text.lower())
        filtered_words = [word for word in words_lower if word not in self.stop_words and len(word) > 2]
        word_freq = Counter(filtered_words)
        common_words = word_freq.most_common(5)
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'common_words': common_words,
            'reading_time_minutes': round(word_count / 200, 1),  # 200 words per minute
            'nltk_available': NLTK_AVAILABLE
        }
    
    def shorten_text(self, text: str, max_sentences: int = 3, max_words: int = 100) -> str:
        """
        Shorten text by extracting key sentences.
        
        Args:
            text: Input text to shorten
            max_sentences: Maximum number of sentences to keep
            max_words: Maximum total words in shortened text
            
        Returns:
            Shortened version of the text
        """
        if not text.strip():
            return text
        
        # Tokenize into sentences with fallback
        if NLTK_AVAILABLE:
            try:
                sentences = sent_tokenize(text)
            except:
                sentences = self._simple_sent_tokenize(text)
        else:
            sentences = self._simple_sent_tokenize(text)
        
        if len(sentences) <= max_sentences:
            # If text is already short, return as is
            return text
        
        # Simple summarization: take first and last sentences
        key_sentences = []
        
        # Add first sentence (usually contains main idea)
        if sentences:
            key_sentences.append(sentences[0])
        
        # Add last sentence (often contains conclusion)
        if len(sentences) > 1:
            key_sentences.append(sentences[-1])
        
        # Add middle sentences if needed, prioritizing longer ones
        if len(sentences) > 2 and len(key_sentences) < max_sentences:
            middle_sentences = sentences[1:-1]
            # Sort by length (longer sentences often contain more information)
            middle_sentences.sort(key=len, reverse=True)
            for sentence in middle_sentences:
                if len(key_sentences) < max_sentences:
                    key_sentences.append(sentence)
                else:
                    break
        
        # Combine and limit word count
        shortened_text = ' '.join(key_sentences)
        words = shortened_text.split()
        
        if len(words) > max_words:
            shortened_text = ' '.join(words[:max_words]) + '...'
        
        return shortened_text
    
    def is_text_too_long(self, text: str, max_words: int = 150) -> bool:
        """
        Check if text exceeds reasonable length for TTS.
        
        Args:
            text: Text to check
            max_words: Maximum allowed words
            
        Returns:
            Boolean indicating if text is too long
        """
        return len(text.split()) > max_words


class TTSEngine:
    """Handles text-to-speech conversion with text analysis."""
    
    def __init__(self):
        self.voices = AVAILABLE_VOICES
        self.analyzer = TextAnalyzer()
        
        # Initialize IBM Watson TTS if available
        self.ibm_tts = None
        if IBM_TTS_AVAILABLE:
            try:
                authenticator = IAMAuthenticator(IBM_TTS_API_KEY)
                self.ibm_tts = TextToSpeechV1(authenticator=authenticator)
                self.ibm_tts.set_service_url(IBM_TTS_URL)
            except Exception as e:
                print(f"Error initializing IBM TTS: {e}")
                self.ibm_tts = None
    
    def generate_audio(self, text: str, voice: str, tone: str, language: str,
                      auto_shorten: bool = True, podcast_mode: bool = False) -> Dict[str, Any]:
        """
        Generate audio from text with optional text shortening.
        
        Args:
            text: Text to convert to speech
            voice: Voice name
            tone: Tone used
            language: Selected language
            auto_shorten: Whether to automatically shorten long text
            podcast_mode: Whether to apply podcast enhancements
            
        Returns:
            Dictionary containing audio path and analysis results
        """
        # Get available voices for the selected language
        language_voices = self.voices.get(language, self.voices["English"])
        
        if voice not in language_voices:
            # Fallback to default voice for the language
            voice = list(language_voices.keys())[0]
        
        try:
            # Analyze the input text
            analysis = self.analyzer.analyze_text(text)
            
            # Check if text needs shortening
            processed_text = text
            was_shortened = False
            
            if auto_shorten and self.analyzer.is_text_too_long(text):
                processed_text = self.analyzer.shorten_text(text)
                was_shortened = True
                # Re-analyze shortened text
                analysis = self.analyzer.analyze_text(processed_text)
                analysis['was_shortened'] = was_shortened
                analysis['original_word_count'] = len(text.split())
            
            # Generate audio
            audio_path = self._generate_audio_file(processed_text, voice, tone, language)
            
            # Apply podcast enhancements if requested
            if podcast_mode:
                try:
                    from utils import create_podcast_audio
                    audio_path = create_podcast_audio(audio_path, processed_text, tone, voice)
                    analysis['podcast_enhanced'] = True
                except Exception as e:
                    print(f"Podcast enhancement failed: {e}")
                    analysis['podcast_enhanced'] = False
            else:
                analysis['podcast_enhanced'] = False
            
            # Index the content for search
            try:
                search_engine = get_search_engine()
                # Use the first few words as title
                title_words = text.split()[:5]
                title = " ".join(title_words) + ("..." if len(text.split()) > 5 else "")
                
                search_engine.index_content(
                    title=title,
                    original_text=text,
                    rewritten_text=processed_text,
                    tone=tone,
                    voice=voice,
                    audio_path=audio_path,
                    word_count=analysis['word_count'],
                    duration_minutes=analysis['reading_time_minutes']
                )
            except Exception as e:
                print(f"Error indexing content: {e}")
            
            return {
                'audio_path': audio_path,
                'processed_text': processed_text,
                'analysis': analysis,
                'success': True
            }
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            # Still try to analyze the text even if audio generation fails
            try:
                analysis = self.analyzer.analyze_text(text)
            except:
                analysis = {
                    'char_count': len(text),
                    'word_count': len(text.split()),
                    'sentence_count': 1,
                    'common_words': [],
                    'reading_time_minutes': 0,
                    'nltk_available': False
                }
            
            return {
                'audio_path': None,
                'processed_text': text,
                'analysis': analysis,
                'success': False,
                'error': str(e)
            }
    
    def get_voice_info(self, voice: str, language: str) -> Dict[str, Any]:
        """
        Get information about a specific voice.
        
        Args:
            voice: Voice name
            language: Language name
            
        Returns:
            Voice configuration dictionary
        """
        language_voices = self.voices.get(language, self.voices["English"])
        return language_voices.get(voice, {})
    
    def _generate_audio_file(self, text: str, voice: str, tone: str, language: str) -> str:
        """
        Generate audio using IBM Watson TTS or fallback to gTTS.
        
        Args:
            text: Text to convert
            voice: Selected voice
            tone: Selected tone
            language: Selected language
            
        Returns:
            Path to generated audio file
        """
        # Generate filename
        filename = generate_filename("audiobook", tone, voice, ".mp3")
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Ensure directory exists
        os.makedirs(AUDIO_DIR, exist_ok=True)

        # Try to use IBM Watson TTS if available
        if self.ibm_tts:
            try:
                language_voices = self.voices.get(language, self.voices["English"])
                voice_config = language_voices.get(voice, list(language_voices.values())[0])
                voice_code = voice_config["voice"]
                
                # Generate audio with IBM Watson TTS
                with open(filepath, 'wb') as audio_file:
                    response = self.ibm_tts.synthesize(
                        text,
                        voice=voice_code,
                        accept='audio/mp3'
                    ).get_result()
                    audio_file.write(response.content)
                
                return filepath
            except Exception as e:
                print(f"IBM TTS failed, falling back to gTTS: {e}")
        
        # Fallback to gTTS
        return self._generate_audio_with_gtts(text, voice, language, filepath)
    
    def _generate_audio_with_gtts(self, text: str, voice: str, language: str, filepath: str) -> str:
        """
        Generate audio using gTTS as fallback.
        
        Args:
            text: Text to convert
            voice: Selected voice
            language: Selected language
            filepath: Path to save the audio file
            
        Returns:
            Path to generated audio file
        """
        # Get language code
        lang_code = SUPPORTED_LANGUAGES.get(language, {}).get("code", "en")
        
        # For gTTS, we can only specify language, not specific voices
        # But we can use different parameters for male/female voices in some languages
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(filepath)
        
        return filepath


# Singleton instance
_tts_engine_instance = None

def get_tts_engine() -> TTSEngine:
    """Get singleton instance of TTSEngine."""
    global _tts_engine_instance
    if _tts_engine_instance is None:
        _tts_engine_instance = TTSEngine()
    return _tts_engine_instance