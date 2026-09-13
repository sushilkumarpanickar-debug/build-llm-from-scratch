"""
Text Processing Skill: Extract, clean, and transform text
Zero-token execution - no LLM calls
"""

import re
from typing import Any, Dict
from loguru import logger

from skills.skill_base import Skill, SkillInput, SkillOutput, SkillType


class TextProcessingSkill(Skill):
    """Process and transform text data without LLM calls."""
    
    def __init__(self):
        super().__init__(
            name="Text Processing",
            skill_type=SkillType.TRANSFORMATION,
            description="Clean, extract, and transform text data",
            version="1.0",
            slug="text-processing",
            input_schema={"text": "string (required)", "action": "clean | extract | tokenize"},
            routing_rules={
                "success:true": ["Knowledge Retrieval", "Data Analysis"],
                "success:false": [],
            }
        )
    
    def execute(self, skill_input: SkillInput) -> SkillOutput:
        """Execute text processing."""
        
        output = SkillOutput()
        text = skill_input.data.get("text", "")
        action = skill_input.data.get("action", "clean")
        
        try:
            if action == "clean":
                result = self._clean_text(text)
            elif action == "extract":
                result = self._extract_entities(text)
            elif action == "tokenize":
                result = self._tokenize_text(text)
            else:
                result = self._clean_text(text)
            
            output.output_data = result
            
        except Exception as e:
            logger.error(f"Text processing failed: {str(e)}")
            output.output_data = {"error": str(e)}
        
        return output
    
    def can_handle(self, task_description: str) -> bool:
        """Check if this skill can handle the task."""
        keywords = ["text", "process", "clean", "extract", "parse", "transform"]
        return any(kw in task_description.lower() for kw in keywords)
    
    def _clean_text(self, text: str) -> Dict[str, Any]:
        """Clean and normalize text."""
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        # Remove special characters but keep alphanumeric and basic punctuation
        cleaned = re.sub(r'[^\w\s\.\,\!\?\-]', '', cleaned)
        
        return {
            "success": True,
            "action": "clean",
            "original_length": len(text),
            "cleaned_length": len(cleaned),
            "cleaned_text": cleaned,
            "reduction_percent": round(100 * (1 - len(cleaned) / max(len(text), 1)), 2),
        }
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text (simplified)."""
        
        # Simple pattern matching for URLs, emails, numbers
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+', text)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        
        # Extract sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            "success": True,
            "action": "extract",
            "entities": {
                "urls": urls,
                "emails": emails,
                "numbers": numbers,
            },
            "sentence_count": len(sentences),
            "sentences": sentences[:5],  # First 5 sentences
        }
    
    def _tokenize_text(self, text: str) -> Dict[str, Any]:
        """Split text into tokens."""
        
        # Simple word tokenization
        words = text.lower().split()
        unique_words = set(words)
        
        return {
            "success": True,
            "action": "tokenize",
            "word_count": len(words),
            "unique_words": len(unique_words),
            "vocabulary": list(unique_words)[:20],  # First 20 unique words
            "tokens": words,
        }
