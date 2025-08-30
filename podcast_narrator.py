# podcast_narrator.py
"""AI Podcast Narrator module for EchoVerse application."""

import streamlit as st
import requests
import json
import time  # Added missing import
from typing import Dict, Any
from config import HUGGINGFACE_API_KEY, HUGGINGFACE_API_URL, AI_SERVICE, PODCAST_STYLES

class PodcastNarrator:
    """Transforms content into engaging podcast scripts using AI."""
    
    def __init__(self):
        self.api_key = HUGGINGFACE_API_KEY
        self.api_url = HUGGINGFACE_API_URL
    
    def generate_podcast_script(self, content: str, topic: str = "", style: str = "Educational") -> str:
        """
        Generate a podcast-style script from the given content using AI.
        
        Args:
            content: The text content to transform into a podcast script
            topic: Optional topic description for context
            style: Podcast style (Conversational, Educational, Storytelling, News, Interview)
            
        Returns:
            Formatted podcast script
        """
        # Use a more specific model for conversation and explanation
        model = "microsoft/DialoGPT-medium"  # Use a reliable model
        
        # Create a more detailed prompt based on style
        style_prompts = {
            "Conversational": "Create a friendly, chatty podcast script like a casual conversation between friends.",
            "Educational": "Create an informative, educational podcast script that explains concepts clearly.",
            "Storytelling": "Create a narrative podcast script with dramatic elements and storytelling techniques.",
            "News": "Create a formal, news-style podcast script with authoritative reporting.",
            "Interview": "Create an interview-style podcast script with questions and answers."
        }
        
        style_prompt = style_prompts.get(style, style_prompts["Educational"])
        
        prompt = f"""
        Transform the following content into an engaging podcast script. 
        {style_prompt}
        
        Guidelines:
        - Use a conversational tone appropriate for the {style.lower()} style
        - Break down complex ideas into simple, digestible parts
        - Use analogies and examples to make concepts relatable
        - Add a brief introduction and conclusion
        - Keep it engaging and easy to follow
        
        Topic: {topic if topic else 'General explanation'}
        Style: {style}
        
        Content to transform:
        {content}
        
        Podcast Script:
        """
        
        try:
            # Try to use Hugging Face API for better results
            if self.api_key:
                script = self._make_huggingface_request(prompt, model)
                if script and script != content:
                    return script
            
            # Fallback to simulated response if API fails or not configured
            return self._create_podcast_script(content, topic, style)
            
        except Exception as e:
            print(f"Error generating podcast script: {e}")
            return self._create_podcast_script(content, topic, style)
    
    def _make_huggingface_request(self, prompt: str, model: str, max_retries: int = 2) -> str:
        """Make API request to Hugging Face for podcast script generation."""
        api_url = f"{self.api_url}/{model}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 600,
                "temperature": 0.8,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=45
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "").strip()
                    elif isinstance(result, dict):
                        return result.get("generated_text", "").strip()
                else:
                    print(f"Hugging Face API request failed with status {response.status_code}")
                    # Fallback to simulation if API fails
                    return self._create_podcast_script(prompt.split("Content to transform:")[-1] if "Content to transform:" in prompt else prompt, "", "Educational")
                    
            except requests.exceptions.RequestException as e:
                print(f"Hugging Face Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    
        return self._create_podcast_script(prompt.split("Content to transform:")[-1] if "Content to transform:" in prompt else prompt, "", "Educational")
    
    def _create_podcast_script(self, content: str, topic: str, style: str) -> str:
        """Create a podcast script with proper formatting and structure."""
        # Clean and prepare the content
        paragraphs = [p for p in content.split('\n') if p.strip()]
        
        # Create introduction based on style
        if style == "Educational":
            intro = f"Welcome to the EchoVerse Podcast. I'm your host, and today we're exploring {topic.lower() if topic else 'an important topic'}.\n\n"
        elif style == "Conversational":
            intro = f"Hey there! Welcome to the show. Today we're chatting about {topic.lower() if topic else 'something really interesting'}.\n\n"
        elif style == "Storytelling":
            intro = f"Gather round, listeners. Today's story is about {topic.lower() if topic else 'a remarkable journey'}.\n\n"
        elif style == "News":
            intro = f"This is EchoVerse News. Our top story today: {topic.lower() if topic else 'important developments'}.\n\n"
        elif style == "Interview":
            intro = f"Welcome to EchoVerse Interviews. Today we're speaking with an expert about {topic.lower() if topic else 'their field of expertise'}.\n\n"
        else:
            intro = f"Welcome to EchoVerse Podcast. Today we're discussing {topic.lower() if topic else 'an important topic'}.\n\n"
        
        intro += "Let's dive right in.\n\n"
        
        # Transform content into podcast format based on style
        podcast_content = []
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                # Add style-specific elements
                if style == "Educational":
                    if i == 0:
                        podcast_content.append(f"To begin with, {paragraph.strip()}")
                    else:
                        podcast_content.append(f"Another important point: {paragraph.strip()}")
                elif style == "Conversational":
                    if i == 0:
                        podcast_content.append(f"So, here's the thing: {paragraph.strip()}")
                    else:
                        podcast_content.append(f"And you know what else? {paragraph.strip()}")
                elif style == "Storytelling":
                    podcast_content.append(f"As the story goes, {paragraph.strip()}")
                elif style == "News":
                    podcast_content.append(f"Reports indicate that {paragraph.strip()}")
                elif style == "Interview":
                    podcast_content.append(f"Our expert explains: {paragraph.strip()}")
                else:
                    podcast_content.append(paragraph.strip())
        
        # Add conclusion based on style
        if style == "Educational":
            outro = "\n\nAnd that's our lesson for today. I hope you found this information helpful and informative."
        elif style == "Conversational":
            outro = "\n\nWell, that's all the time we have for today. Thanks for hanging out and chatting with me!"
        elif style == "Storytelling":
            outro = "\n\nAnd so our story comes to an end, but the lessons remain with us."
        elif style == "News":
            outro = "\n\nThat's all for this edition of EchoVerse News. Stay tuned for more updates."
        elif style == "Interview":
            outro = "\n\nThank you to our expert for sharing those valuable insights with us today."
        else:
            outro = "\n\nAnd that brings us to the end of today's discussion. Thank you for listening."
        
        outro += "\n\nThis has been an EchoVerse production."
        
        return intro + ' '.join(podcast_content) + outro

# Singleton instance
_podcast_narrator_instance = None

def get_podcast_narrator() -> PodcastNarrator:
    """Get singleton instance of PodcastNarrator."""
    global _podcast_narrator_instance
    if _podcast_narrator_instance is None:
        _podcast_narrator_instance = PodcastNarrator()
    return _podcast_narrator_instance