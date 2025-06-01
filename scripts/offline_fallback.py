
import json
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

class OfflineFallbackSystem:
    """Offline fallback system for when OpenAI API is unavailable"""
    
    def __init__(self):
        self.db_path = "data/offline_cache.db"
        self.facts_cache = "data/cached_facts.json"
        self.common_responses = "data/common_responses.json"
        self.init_database()
        self.load_common_responses()
    
    def init_database(self):
        """Initialize SQLite database for offline cache"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                timestamp TEXT,
                usage_count INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                content TEXT,
                confidence REAL,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_common_responses(self):
        """Load common response templates"""
        try:
            with open(self.common_responses, 'r') as f:
                self.response_templates = json.load(f)
        except FileNotFoundError:
            self.response_templates = {
                "greeting": [
                    "Hello Michael! I'm currently in offline mode, but I can still help with cached information.",
                    "Hi there! While I can't access live data right now, I have your personal information available."
                ],
                "personal_question": [
                    "Based on what I know about you, {fact}. However, I'm currently offline so I can't access the latest information.",
                    "From your previous interactions, {fact}. I'm in offline mode right now."
                ],
                "general_question": [
                    "I'm currently in offline mode and can't provide real-time information. Here's what I can tell you from cached data: {info}",
                    "While I'm offline, I can share some general guidance: {info}"
                ],
                "no_data": [
                    "I'm currently in offline mode and don't have cached information about that topic. Please try again when I'm back online.",
                    "I don't have that information cached locally. I'll be able to help better once I'm back online."
                ]
            }
    
    def cache_response(self, question: str, answer: str):
        """Cache a successful response for offline use"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if similar question exists
        cursor.execute('''
            SELECT id, usage_count FROM cached_responses 
            WHERE question = ? OR LOWER(question) LIKE LOWER(?)
        ''', (question, f"%{question[:20]}%"))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update usage count
            cursor.execute('''
                UPDATE cached_responses 
                SET usage_count = usage_count + 1, timestamp = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), existing[0]))
        else:
            # Insert new response
            cursor.execute('''
                INSERT INTO cached_responses (question, answer, timestamp)
                VALUES (?, ?, ?)
            ''', (question, answer, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_cached_response(self, question: str) -> Optional[str]:
        """Get cached response for similar question"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Try exact match first
        cursor.execute('''
            SELECT answer FROM cached_responses 
            WHERE LOWER(question) = LOWER(?)
            ORDER BY usage_count DESC, timestamp DESC
            LIMIT 1
        ''', (question,))
        
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]
        
        # Try fuzzy matching with keywords
        keywords = self.extract_keywords(question)
        if keywords:
            placeholders = ' OR '.join(['LOWER(question) LIKE LOWER(?)'] * len(keywords))
            keyword_patterns = [f"%{keyword}%" for keyword in keywords]
            
            cursor.execute(f'''
                SELECT answer FROM cached_responses 
                WHERE {placeholders}
                ORDER BY usage_count DESC, timestamp DESC
                LIMIT 1
            ''', keyword_patterns)
            
            result = cursor.fetchone()
            if result:
                conn.close()
                return f"Based on similar previous questions: {result[0]}"
        
        conn.close()
        return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract key words from question"""
        # Remove common words
        stop_words = {'what', 'how', 'when', 'where', 'why', 'who', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'can', 'could', 'should', 'would', 'will', 'shall', 'may', 'might', 'must', 'do', 'does', 'did', 'have', 'has', 'had', 'be', 'been', 'being', 'am', 'was', 'were'}
        
        words = re.findall(r'\w+', text.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:5]  # Top 5 keywords
    
    def cache_personal_fact(self, fact_type: str, content: str, confidence: float):
        """Cache personal fact for offline use"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO personal_facts (type, content, confidence, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (fact_type, content, confidence, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_personal_facts(self, fact_type: str = None) -> List[Dict[str, Any]]:
        """Get cached personal facts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if fact_type:
            cursor.execute('''
                SELECT type, content, confidence FROM personal_facts 
                WHERE type = ?
                ORDER BY confidence DESC
            ''', (fact_type,))
        else:
            cursor.execute('''
                SELECT type, content, confidence FROM personal_facts 
                ORDER BY confidence DESC, timestamp DESC
            ''')
        
        facts = []
        for row in cursor.fetchall():
            facts.append({
                "type": row[0],
                "content": row[1],
                "confidence": row[2]
            })
        
        conn.close()
        return facts
    
    def generate_offline_response(self, question: str) -> str:
        """Generate response using offline data"""
        # First try cached responses
        cached = self.get_cached_response(question)
        if cached:
            return f"[OFFLINE MODE] {cached}"
        
        # Check if it's a personal question
        personal_keywords = ['my', 'i am', 'i have', 'tell me about', 'what do you know']
        is_personal = any(keyword in question.lower() for keyword in personal_keywords)
        
        if is_personal:
            facts = self.get_personal_facts()
            if facts:
                relevant_fact = facts[0]  # Get highest confidence fact
                template = self.response_templates["personal_question"][0]
                return f"[OFFLINE MODE] {template.format(fact=relevant_fact['content'])}"
        
        # Check for specific question types
        if any(word in question.lower() for word in ['calendar', 'schedule', 'meeting']):
            return "[OFFLINE MODE] I can't access your calendar while offline. Please check your Google Calendar directly or try again when I'm back online."
        
        if any(word in question.lower() for word in ['email', 'message', 'communication']):
            return "[OFFLINE MODE] I can't check your emails while offline. Please check your Gmail directly or try again when I'm back online."
        
        if any(word in question.lower() for word in ['weather', 'temperature']):
            return "[OFFLINE MODE] I can't get current weather data while offline. Please check a weather app or try again when I'm back online."
        
        # Default response
        template = self.response_templates["no_data"][0]
        return f"[OFFLINE MODE] {template}"
    
    def is_online(self) -> bool:
        """Check if system should use online or offline mode"""
        try:
            import urllib.request
            urllib.request.urlopen('https://api.openai.com', timeout=5)
            return True
        except:
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get offline system status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM cached_responses')
        cached_responses = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM personal_facts')
        personal_facts = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "offline_mode_available": True,
            "cached_responses": cached_responses,
            "personal_facts": personal_facts,
            "last_cache_update": datetime.now().isoformat()
        }

# Global instance
offline_system = OfflineFallbackSystem()
