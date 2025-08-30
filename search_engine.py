"""Search engine module for EchoVerse application."""

import os
import json
import sqlite3
import re
import urllib.parse
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import AUDIO_DIR, TEMP_DIR
from utils import truncate_text

class SearchEngine:
    """Handles indexing and searching of audiobook content."""
    
    def __init__(self):
        self.db_path = os.path.join(TEMP_DIR, "echoverse_search.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize the search database."""
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                original_text TEXT,
                rewritten_text TEXT,
                tone TEXT,
                voice TEXT,
                audio_path TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER,
                duration_minutes REAL
            )
        ''')
        
        # Create search index table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_index (
                content_id INTEGER,
                token TEXT,
                frequency INTEGER,
                FOREIGN KEY (content_id) REFERENCES content (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_token ON search_index(token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_tone ON content(tone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_voice ON content(voice)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_created ON content(created_at)')
        
        conn.commit()
        conn.close()
    
    def _extract_keywords_from_url(self, query: str) -> str:
        """
        Extract meaningful keywords from URL-like queries.
        
        Args:
            query: Potential URL or text query
            
        Returns:
            Extracted keywords for searching
        """
        # Check if it looks like a URL
        url_pattern = r'https?://[^\s]+'
        if re.match(url_pattern, query):
            try:
                # Parse URL and extract meaningful parts
                parsed_url = urllib.parse.urlparse(query)
                path_parts = parsed_url.path.split('/')
                
                # Get the last meaningful part of the path (usually the title)
                keywords = []
                for part in reversed(path_parts):
                    if part and part not in ['wiki', 'wikipedia', 'page', 'article']:
                        # Replace underscores and hyphens with spaces
                        clean_part = part.replace('_', ' ').replace('-', ' ').replace('%20', ' ')
                        keywords.append(clean_part)
                        break
                
                return ' '.join(keywords) if keywords else query
            except:
                return query
        
        return query
    
    def index_content(self, title: str, original_text: str, rewritten_text: str, 
                     tone: str, voice: str, audio_path: str, word_count: int, 
                     duration_minutes: float) -> bool:
        """
        Index content for searching.
        
        Args:
            title: Content title
            original_text: Original text content
            rewritten_text: AI-rewritten text
            tone: Selected tone
            voice: Selected voice
            audio_path: Path to audio file
            word_count: Number of words
            duration_minutes: Audio duration in minutes
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if content already exists
            cursor.execute(
                "SELECT id FROM content WHERE audio_path = ?",
                (audio_path,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE content 
                    SET title = ?, original_text = ?, rewritten_text = ?, 
                        tone = ?, voice = ?, word_count = ?, duration_minutes = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE audio_path = ?
                ''', (title, original_text, rewritten_text, tone, voice, 
                      word_count, duration_minutes, audio_path))
                content_id = existing[0]
                
                # Remove old search index
                cursor.execute(
                    "DELETE FROM search_index WHERE content_id = ?",
                    (content_id,)
                )
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO content 
                    (title, original_text, rewritten_text, tone, voice, audio_path, word_count, duration_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, original_text, rewritten_text, tone, voice, 
                      audio_path, word_count, duration_minutes))
                content_id = cursor.lastrowid
            
            # Index text content
            self._index_text_content(cursor, content_id, original_text + " " + rewritten_text)
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error indexing content: {e}")
            return False
        finally:
            conn.close()
    
    def _index_text_content(self, cursor, content_id: int, text: str):
        """Index text content for searching."""
        # Simple tokenization (improve with NLTK if available)
        tokens = self._tokenize_text(text.lower())
        token_freq = {}
        
        # Count token frequencies
        for token in tokens:
            if len(token) > 2:  # Ignore very short tokens
                token_freq[token] = token_freq.get(token, 0) + 1
        
        # Insert into search index
        for token, frequency in token_freq.items():
            cursor.execute(
                "INSERT INTO search_index (content_id, token, frequency) VALUES (?, ?, ?)",
                (content_id, token, frequency)
            )
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Simple text tokenization."""
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text)
        return words
    
    def search_content(self, query: str, tone_filter: Optional[str] = None, 
                      voice_filter: Optional[str] = None, 
                      date_filter: Optional[str] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search indexed content.
        
        Args:
            query: Search query (can be URL or text)
            tone_filter: Filter by tone
            voice_filter: Filter by voice
            date_filter: Filter by date ('today', 'week', 'month', 'year')
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Preprocess query - extract keywords if it's a URL
            processed_query = self._extract_keywords_from_url(query)
            search_tokens = self._tokenize_text(processed_query.lower())
            
            if not search_tokens:
                # If no search tokens, return recent content
                sql = '''
                    SELECT c.id, c.title, c.original_text, c.rewritten_text, 
                           c.tone, c.voice, c.audio_path, c.created_at,
                           c.word_count, c.duration_minutes
                    FROM content c
                '''
                params = []
            else:
                # Build search with relevance scoring
                sql = '''
                    SELECT c.id, c.title, c.original_text, c.rewritten_text, 
                           c.tone, c.voice, c.audio_path, c.created_at,
                           c.word_count, c.duration_minutes,
                           SUM(si.frequency) as relevance
                    FROM content c
                    JOIN search_index si ON c.id = si.content_id
                    WHERE si.token IN ({})
                '''.format(','.join(['?'] * len(search_tokens)))
                
                params = search_tokens
            
            # Add filters
            where_clauses = []
            
            if tone_filter:
                where_clauses.append("c.tone = ?")
                params.append(tone_filter)
            
            if voice_filter:
                where_clauses.append("c.voice = ?")
                params.append(voice_filter)
            
            if date_filter:
                date_condition = self._get_date_filter_condition(date_filter)
                if date_condition:
                    where_clauses.append(date_condition)
            
            if where_clauses:
                sql += " AND " + " AND ".join(where_clauses)
            
            # Group and order
            if search_tokens:
                sql += '''
                    GROUP BY c.id
                    ORDER BY relevance DESC, c.created_at DESC
                '''
            else:
                sql += " ORDER BY c.created_at DESC"
            
            sql += " LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'id': row[0],
                    'title': row[1],
                    'original_text': row[2],
                    'rewritten_text': row[3],
                    'tone': row[4],
                    'voice': row[5],
                    'audio_path': row[6],
                    'created_at': row[7],
                    'word_count': row[8],
                    'duration_minutes': row[9],
                    'preview': truncate_text(row[2] or row[3], 150)
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching content: {e}")
            return []
        finally:
            conn.close()
    
    def _get_date_filter_condition(self, date_filter: str) -> Optional[str]:
        """Get SQL condition for date filter."""
        conditions = {
            'today': "DATE(c.created_at) = DATE('now')",
            'week': "c.created_at >= DATE('now', '-7 days')",
            'month': "c.created_at >= DATE('now', '-30 days')",
            'year': "c.created_at >= DATE('now', '-365 days')"
        }
        return conditions.get(date_filter.lower())
    
    def get_recent_content(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently created content."""
        return self.search_content("", limit=limit)
    
    def get_content_by_id(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Get content by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, original_text, rewritten_text, tone, voice,
                       audio_path, created_at, word_count, duration_minutes
                FROM content 
                WHERE id = ?
            ''', (content_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'original_text': row[2],
                    'rewritten_text': row[3],
                    'tone': row[4],
                    'voice': row[5],
                    'audio_path': row[6],
                    'created_at': row[7],
                    'word_count': row[8],
                    'duration_minutes': row[9]
                }
            return None
            
        except Exception as e:
            print(f"Error getting content by ID: {e}")
            return None
        finally:
            conn.close()
    
    def delete_content(self, content_id: int) -> bool:
        """Delete content from index."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM search_index WHERE content_id = ?", (content_id,))
            cursor.execute("DELETE FROM content WHERE id = ?", (content_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error deleting content: {e}")
            return False
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total content count
            cursor.execute("SELECT COUNT(*) FROM content")
            stats['total_content'] = cursor.fetchone()[0] or 0
            
            # Content by tone
            cursor.execute("SELECT tone, COUNT(*) FROM content GROUP BY tone")
            stats['content_by_tone'] = dict(cursor.fetchall())
            
            # Content by voice
            cursor.execute("SELECT voice, COUNT(*) FROM content GROUP BY voice")
            stats['content_by_voice'] = dict(cursor.fetchall())
            
            # Total words
            cursor.execute("SELECT SUM(word_count) FROM content")
            stats['total_words'] = cursor.fetchone()[0] or 0
            
            # Total duration
            cursor.execute("SELECT SUM(duration_minutes) FROM content")
            stats['total_duration_minutes'] = cursor.fetchone()[0] or 0.0
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_content': 0,
                'total_words': 0,
                'total_duration_minutes': 0.0,
                'content_by_tone': {},
                'content_by_voice': {}
            }
        finally:
            conn.close()

# Singleton instance
_search_engine_instance = None

def get_search_engine() -> SearchEngine:
    """Get singleton instance of SearchEngine."""
    global _search_engine_instance
    if _search_engine_instance is None:
        _search_engine_instance = SearchEngine()
    return _search_engine_instance