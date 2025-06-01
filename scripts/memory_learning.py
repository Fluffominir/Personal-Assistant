
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import openai
from dataclasses import dataclass
import asyncio
import schedule
import time

@dataclass
class Interaction:
    question: str
    answer: str
    timestamp: str
    feedback: str = None
    context_type: str = "general"

@dataclass
class PersonalFact:
    type: str  # preference, goal, habit, trait, relationship
    content: str
    confidence: float
    source_interactions: List[str]
    last_updated: str

class MemoryLearningSystem:
    def __init__(self):
        self.openai_client = openai.OpenAI() if os.environ.get("OPENAI_API_KEY") else None
        self.interactions_file = "data/interactions.json"
        self.facts_file = "data/personal_facts.json"
        self.memory_index_file = "data/memory_index.json"
        
    def load_interactions(self) -> List[Interaction]:
        """Load stored interactions"""
        try:
            with open(self.interactions_file, 'r') as f:
                data = json.load(f)
                return [Interaction(**item) for item in data]
        except FileNotFoundError:
            return []
    
    def save_interactions(self, interactions: List[Interaction]):
        """Save interactions to file"""
        os.makedirs(os.path.dirname(self.interactions_file), exist_ok=True)
        with open(self.interactions_file, 'w') as f:
            json.dump([vars(i) for i in interactions], f, indent=2)
    
    def load_facts(self) -> List[PersonalFact]:
        """Load personal facts"""
        try:
            with open(self.facts_file, 'r') as f:
                data = json.load(f)
                return [PersonalFact(**item) for item in data]
        except FileNotFoundError:
            return []
    
    def save_facts(self, facts: List[PersonalFact]):
        """Save personal facts to file"""
        os.makedirs(os.path.dirname(self.facts_file), exist_ok=True)
        with open(self.facts_file, 'w') as f:
            json.dump([vars(f) for f in facts], f, indent=2)
    
    def add_interaction(self, question: str, answer: str, context_type: str = "general"):
        """Add new interaction"""
        interactions = self.load_interactions()
        interaction = Interaction(
            question=question,
            answer=answer,
            timestamp=datetime.now().isoformat(),
            context_type=context_type
        )
        interactions.append(interaction)
        
        # Keep only last 1000 interactions
        if len(interactions) > 1000:
            interactions = interactions[-1000:]
        
        self.save_interactions(interactions)
        return interaction
    
    async def extract_facts_from_interactions(self, interactions: List[Interaction]) -> List[PersonalFact]:
        """Extract personal facts from interactions using LLM"""
        if not self.openai_client:
            return []
        
        # Group recent interactions for analysis
        recent_interactions = [i for i in interactions if 
                             datetime.fromisoformat(i.timestamp) > datetime.now() - timedelta(days=30)]
        
        if not recent_interactions:
            return []
        
        # Prepare context for fact extraction
        interaction_text = "\n".join([
            f"Q: {i.question}\nA: {i.answer}\n---"
            for i in recent_interactions[-20:]  # Last 20 interactions
        ])
        
        prompt = f"""
        Analyze these interactions between Michael Slusher and his AI assistant ATLAS.
        Extract key personal facts about Michael including:
        - Preferences (work style, tools, communication)
        - Goals (short-term and long-term)
        - Habits (daily routines, patterns)
        - Traits (personality, strengths, challenges)
        - Relationships (team, clients, family)
        
        Return ONLY a JSON array of facts in this format:
        [
            {{
                "type": "preference|goal|habit|trait|relationship",
                "content": "Clear, specific fact about Michael",
                "confidence": 0.0-1.0
            }}
        ]
        
        Interactions:
        {interaction_text}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a personal fact extraction specialist. Extract only clear, specific facts about Michael."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            facts_data = json.loads(response.choices[0].message.content)
            facts = []
            
            for fact_data in facts_data:
                fact = PersonalFact(
                    type=fact_data["type"],
                    content=fact_data["content"],
                    confidence=fact_data["confidence"],
                    source_interactions=[i.timestamp for i in recent_interactions[-5:]],
                    last_updated=datetime.now().isoformat()
                )
                facts.append(fact)
            
            return facts
            
        except Exception as e:
            print(f"Error extracting facts: {e}")
            return []
    
    def merge_facts(self, existing_facts: List[PersonalFact], new_facts: List[PersonalFact]) -> List[PersonalFact]:
        """Merge new facts with existing ones, updating confidence"""
        merged = {}
        
        # Add existing facts
        for fact in existing_facts:
            key = f"{fact.type}:{fact.content.lower()}"
            merged[key] = fact
        
        # Update with new facts
        for fact in new_facts:
            key = f"{fact.type}:{fact.content.lower()}"
            if key in merged:
                # Update confidence (weighted average)
                existing = merged[key]
                new_confidence = (existing.confidence * 0.7) + (fact.confidence * 0.3)
                existing.confidence = min(1.0, new_confidence)
                existing.last_updated = fact.last_updated
                existing.source_interactions.extend(fact.source_interactions)
                existing.source_interactions = existing.source_interactions[-10:]  # Keep last 10
            else:
                merged[key] = fact
        
        # Filter facts by confidence threshold
        return [fact for fact in merged.values() if fact.confidence > 0.3]
    
    async def daily_memory_audit(self):
        """Daily memory audit and fact extraction"""
        print("🧠 Starting daily memory audit...")
        
        interactions = self.load_interactions()
        existing_facts = self.load_facts()
        
        # Extract new facts from recent interactions
        new_facts = await self.extract_facts_from_interactions(interactions)
        
        # Merge facts
        updated_facts = self.merge_facts(existing_facts, new_facts)
        
        # Save updated facts
        self.save_facts(updated_facts)
        
        print(f"✅ Memory audit complete. {len(updated_facts)} facts stored.")
        return {
            "total_facts": len(updated_facts),
            "new_facts": len(new_facts),
            "high_confidence_facts": len([f for f in updated_facts if f.confidence > 0.8])
        }
    
    def get_relevant_facts(self, query: str, max_facts: int = 5) -> List[PersonalFact]:
        """Get facts relevant to a query"""
        facts = self.load_facts()
        query_lower = query.lower()
        
        # Simple relevance scoring based on keyword matching
        scored_facts = []
        for fact in facts:
            score = 0
            fact_content_lower = fact.content.lower()
            
            # Exact phrase matches
            if any(word in fact_content_lower for word in query_lower.split()):
                score += fact.confidence * 2
            
            # Type relevance
            if fact.type in query_lower:
                score += 0.5
            
            if score > 0:
                scored_facts.append((score, fact))
        
        # Sort by score and return top facts
        scored_facts.sort(key=lambda x: x[0], reverse=True)
        return [fact for score, fact in scored_facts[:max_facts]]
    
    def generate_context_for_query(self, query: str) -> str:
        """Generate context from personal facts for a query"""
        relevant_facts = self.get_relevant_facts(query)
        
        if not relevant_facts:
            return ""
        
        context_parts = ["Personal context about Michael:"]
        for fact in relevant_facts:
            context_parts.append(f"- {fact.content} (confidence: {fact.confidence:.1f})")
        
        return "\n".join(context_parts)

# Global instance
memory_system = MemoryLearningSystem()

# Schedule daily audit
def schedule_daily_audit():
    """Schedule daily memory audit"""
    schedule.every().day.at("03:00").do(lambda: asyncio.run(memory_system.daily_memory_audit()))
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Run daily audit scheduler
    schedule_daily_audit()
