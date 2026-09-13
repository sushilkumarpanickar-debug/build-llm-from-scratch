"""
Synthesis Skill: Combine and synthesize results from multiple sources
Zero-token execution - no LLM calls
"""

from typing import Any, Dict
from loguru import logger

from skills.skill_base import Skill, SkillInput, SkillOutput, SkillType


class SynthesisSkill(Skill):
    """Synthesize and combine data from multiple sources without LLM calls."""
    
    def __init__(self):
        super().__init__(
            name="Synthesis",
            skill_type=SkillType.SYNTHESIS,
            description="Combine and synthesize results from multiple sources",
            version="1.0",
            routing_rules={}
        )
    
    def execute(self, skill_input: SkillInput) -> SkillOutput:
        """Execute synthesis."""
        
        output = SkillOutput()
        data_sources = skill_input.data.get("sources", [])
        synthesis_type = skill_input.data.get("synthesis_type", "combine")
        
        try:
            if synthesis_type == "combine":
                result = self._combine_results(data_sources)
            elif synthesis_type == "format":
                result = self._format_results(data_sources)
            elif synthesis_type == "summarize":
                result = self._summarize_results(data_sources)
            else:
                result = self._combine_results(data_sources)
            
            output.output_data = result
            
        except Exception as e:
            logger.error(f"Synthesis failed: {str(e)}")
            output.output_data = {"error": str(e), "success": False}
        
        return output
    
    def can_handle(self, task_description: str) -> bool:
        """Check if this skill can handle the task."""
        keywords = ["synthesize", "combine", "merge", "aggregate", "format", "summarize"]
        return any(kw in task_description.lower() for kw in keywords)
    
    def _combine_results(self, sources: list) -> Dict[str, Any]:
        """Combine results from multiple sources."""
        
        combined = {
            "success": True,
            "synthesis_type": "combine",
            "source_count": len(sources),
            "sources": sources,
            "combined_data": {}
        }
        
        # Merge all sources
        for source in sources:
            if isinstance(source, dict):
                combined["combined_data"].update(source)
        
        return combined
    
    def _format_results(self, sources: list) -> Dict[str, Any]:
        """Format results into structured output."""
        
        formatted = {
            "success": True,
            "synthesis_type": "format",
            "source_count": len(sources),
            "formatted_output": "",
        }
        
        # Format as structured text
        lines = []
        for idx, source in enumerate(sources, 1):
            if isinstance(source, dict):
                lines.append(f"\n[Source {idx}]:")
                for key, value in source.items():
                    lines.append(f"  {key}: {value}")
        
        formatted["formatted_output"] = "\n".join(lines)
        return formatted
    
    def _summarize_results(self, sources: list) -> Dict[str, Any]:
        """Summarize results from multiple sources."""
        
        summary = {
            "success": True,
            "synthesis_type": "summarize",
            "source_count": len(sources),
            "summary": ""
        }
        
        # Create summary
        summary_lines = [f"Summary of {len(sources)} sources:"]
        
        for idx, source in enumerate(sources, 1):
            if isinstance(source, dict):
                key_count = len(source)
                summary_lines.append(f"  Source {idx}: {key_count} fields")
        
        summary["summary"] = "\n".join(summary_lines)
        return summary
