# text_processor.py
"""Text processing module for tone adaptation using IBM Watsonx or Hugging Face."""

import requests
import json
import time
import streamlit as st
from typing import Optional, Dict, Any
from config import IBM_WATSONX_API_KEY, IBM_WATSONX_API_URL, IBM_WATSONX_PROJECT_ID, AVAILABLE_TONES
from config import HUGGINGFACE_API_KEY, HUGGINGFACE_API_URL, HUGGINGFACE_MODELS, AI_SERVICE


class TextProcessor:
    """Handles text rewriting with different tones using IBM Watsonx or Hugging Face."""
    
    def __init__(self):
        self.api_key = IBM_WATSONX_API_KEY if AI_SERVICE == "ibm" else HUGGINGFACE_API_KEY
        self.api_url = IBM_WATSONX_API_URL if AI_SERVICE == "ibm" else HUGGINGFACE_API_URL
        self.project_id = IBM_WATSONX_PROJECT_ID
        self.session = requests.Session()
        
    def _make_ibm_request(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Make API request to IBM Watsonx.
        """
        if not self.api_key or not self.api_url or not self.project_id:
            return self._simulate_ai_response(prompt)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model_id": "ibm/granite-13b-instruct-v2",
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": 1024,
                "min_new_tokens": 0,
                "repetition_penalty": 1.0
            },
            "project_id": self.project_id
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("results", [{}])[0].get("generated_text", "").strip()
                else:
                    print(f"IBM API request failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"IBM Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
    
    def _make_huggingface_request(self, prompt: str, tone: str, max_retries: int = 3) -> Optional[str]:
        """
        Make API request to Hugging Face Inference API.
        """
        if not self.api_key:
            return self._simulate_ai_response(prompt)
        
        # Use a more reliable model that's likely to be available
        model = "microsoft/DialoGPT-medium"  # Use a consistent model
        
        api_url = f"{self.api_url}/{model}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Format prompt for the model
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 500,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "").strip()
                    elif isinstance(result, dict):
                        return result.get("generated_text", "").strip()
                else:
                    print(f"Hugging Face API request failed with status {response.status_code}: {response.text}")
                    # Fallback to simulation if API fails
                    return self._simulate_ai_response(prompt)
                    
            except requests.exceptions.RequestException as e:
                print(f"Hugging Face Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return self._simulate_ai_response(prompt)
    
    def _simulate_ai_response(self, prompt: str) -> str:
        """
        Simulate AI response for demo purposes.
        """
        # Extract original text from prompt
        original_text = prompt
        for tone_config in AVAILABLE_TONES.values():
            if prompt.startswith(tone_config["prompt"]):
                original_text = prompt[len(tone_config["prompt"]):].strip()
                break
        
        # Determine tone from prompt
        tone = "neutral"
        for tone_name, tone_config in AVAILABLE_TONES.items():
            if prompt.startswith(tone_config["prompt"]):
                tone = tone_name.lower()
                break
        
        # Apply tone transformation
        if tone == "suspenseful":
            return self._apply_suspenseful_tone(original_text)
        elif tone == "inspiring":
            return self._apply_inspiring_tone(original_text)
        else:
            return self._apply_neutral_tone(original_text)
    
    def _apply_neutral_tone(self, text: str) -> str:
        """Apply neutral tone transformation."""
        sentences = text.split('.')
        rewritten = []
        
        for sentence in sentences:
            if sentence.strip():
                clean_sentence = sentence.strip()
                # Make it more formal and educational
                if len(clean_sentence) > 10:
                    clean_sentence = f"It is important to understand that {clean_sentence.lower()}"
                if not clean_sentence.endswith(('.', '!', '?')):
                    clean_sentence += '.'
                rewritten.append(clean_sentence)
        
        return ' '.join(rewritten)
    
    def _apply_suspenseful_tone(self, text: str) -> str:
        """Apply suspenseful tone transformation."""
        sentences = text.split('.')
        rewritten = []
        
        for sentence in sentences:
            if sentence.strip():
                clean_sentence = sentence.strip()
                # Add dramatic elements
                if len(clean_sentence) > 15:
                    clean_sentence = f"In the shadows of uncertainty, {clean_sentence.lower()}"
                clean_sentence += "... but what lies ahead remains a mystery."
                rewritten.append(clean_sentence)
        
        return ' '.join(rewritten)
    
    def _apply_inspiring_tone(self, text: str) -> str:
        """Apply inspiring tone transformation."""
        sentences = text.split('.')
        rewritten = []
        
        for sentence in sentences:
            if sentence.strip():
                clean_sentence = sentence.strip()
                # Add motivational elements
                if len(clean_sentence) > 12:
                    clean_sentence = f"Believe in the power of {clean_sentence.lower()}"
                clean_sentence += "! This is your moment to shine."
                rewritten.append(clean_sentence)
                
        return ' '.join(rewritten)
    
    def rewrite_text(self, original_text: str, tone: str) -> Optional[str]:
        """
        Rewrite text with specified tone using AI service.
        
        Args:
            original_text: The original text to rewrite
            tone: The desired tone (Neutral, Suspenseful, Inspiring)
            
        Returns:
            Rewritten text or None if processing failed
        """
        if tone not in AVAILABLE_TONES:
            raise ValueError(f"Invalid tone. Must be one of: {list(AVAILABLE_TONES.keys())}")
        
        tone_config = AVAILABLE_TONES[tone]
        prompt = f"{tone_config['prompt']}{original_text}"
        
        try:
            if AI_SERVICE == "ibm":
                rewritten_text = self._make_ibm_request(prompt)
            else:  # huggingface
                rewritten_text = self._make_huggingface_request(prompt, tone)
            
            if rewritten_text:
                # Clean up the response
                rewritten_text = rewritten_text.replace("Original text:", "").strip()
                if rewritten_text.startswith("Rewritten text:"):
                    rewritten_text = rewritten_text.replace("Rewritten text:", "").strip()
                
                return rewritten_text if rewritten_text else original_text
            else:
                return original_text  # Fallback to original if API fails
                
        except Exception as e:
            print(f"Error during text rewriting: {e}")
            return original_text  # Fallback to original text
    
    def process_text(self, text: str, tone: str, language: str, auto_shorten: bool = True) -> Dict[str, Any]:
        """
        Process text with AI rewriting and return results.
        
        Args:
            text: Original text to process
            tone: Selected tone for rewriting
            language: Selected language
            auto_shorten: Whether to automatically shorten long text
            
        Returns:
            Dictionary with processing results
        """
        try:
            # For now, we'll just rewrite the text without shortening
            # In a real implementation, you might add language-specific processing
            rewritten_text = self.rewrite_text(text, tone)
            
            return {
                'success': True,
                'rewritten_text': rewritten_text,
                'original_text': text,
                'tone': tone,
                'language': language
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'rewritten_text': text,  # Fallback to original text
                'original_text': text,
                'tone': tone,
                'language': language
            }


def get_text_processor() -> TextProcessor:
    """Get singleton instance of TextProcessor."""
    if 'text_processor' not in st.session_state:
        st.session_state.text_processor = TextProcessor()
    return st.session_state.text_processor