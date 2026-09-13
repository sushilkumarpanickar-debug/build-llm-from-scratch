"""
Data Analysis Skill: Analyze and extract insights from data
Zero-token execution - no LLM calls
"""

import json
from typing import Any, Dict, List
from statistics import mean, median, stdev
from loguru import logger

from skills.skill_base import Skill, SkillInput, SkillOutput, SkillType


class DataAnalysisSkill(Skill):
    """Analyze data and extract insights without LLM calls."""
    
    def __init__(self):
        super().__init__(
            name="Data Analysis",
            skill_type=SkillType.ANALYSIS,
            description="Analyze data and extract statistical insights",
            version="1.0",
            slug="data-analysis",
            input_schema={"data": "object, string, or list (required)", "analysis_type": "general | statistical | pattern | distribution"},
            routing_rules={
                "success:true": ["Synthesis"],
                "success:false": [],
            }
        )
    
    def execute(self, skill_input: SkillInput) -> SkillOutput:
        """Execute data analysis."""
        
        output = SkillOutput()
        data = skill_input.data.get("data", {})
        analysis_type = skill_input.data.get("analysis_type", "general")
        
        try:
            if analysis_type == "statistical":
                result = self._statistical_analysis(data)
            elif analysis_type == "pattern":
                result = self._pattern_analysis(data)
            elif analysis_type == "distribution":
                result = self._distribution_analysis(data)
            else:
                result = self._general_analysis(data)
            
            output.output_data = result
            
        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            output.output_data = {"error": str(e), "success": False}
        
        return output
    
    def can_handle(self, task_description: str) -> bool:
        """Check if this skill can handle the task."""
        keywords = ["analyze", "analysis", "insight", "statistics", "pattern", "trend"]
        return any(kw in task_description.lower() for kw in keywords)
    
    def _general_analysis(self, data: Any) -> Dict[str, Any]:
        """General data analysis."""
        
        analysis = {
            "success": True,
            "analysis_type": "general",
            "data_type": type(data).__name__,
        }
        
        if isinstance(data, dict):
            analysis["keys"] = list(data.keys())
            analysis["key_count"] = len(data)
        elif isinstance(data, list):
            analysis["item_count"] = len(data)
            if data and isinstance(data[0], (int, float)):
                analysis["min"] = min(data)
                analysis["max"] = max(data)
                analysis["avg"] = sum(data) / len(data)
        elif isinstance(data, str):
            analysis["length"] = len(data)
            analysis["word_count"] = len(data.split())
        
        return analysis
    
    def _statistical_analysis(self, data: Any) -> Dict[str, Any]:
        """Perform statistical analysis on numerical data."""
        
        if not isinstance(data, list):
            return {"error": "Data must be a list for statistical analysis", "success": False}
        
        try:
            # Filter numeric values
            numeric_data = [x for x in data if isinstance(x, (int, float))]
            
            if not numeric_data:
                return {"error": "No numeric data found", "success": False}
            
            analysis = {
                "success": True,
                "analysis_type": "statistical",
                "count": len(numeric_data),
                "sum": sum(numeric_data),
                "mean": mean(numeric_data),
                "median": median(numeric_data),
                "min": min(numeric_data),
                "max": max(numeric_data),
                "range": max(numeric_data) - min(numeric_data),
            }
            
            if len(numeric_data) > 1:
                analysis["stdev"] = stdev(numeric_data)
            
            return analysis
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _pattern_analysis(self, data: Any) -> Dict[str, Any]:
        """Identify patterns in data."""
        
        if isinstance(data, list):
            # Check for sequences
            if len(data) > 1 and isinstance(data[0], (int, float)):
                differences = [data[i+1] - data[i] for i in range(len(data)-1)]
                
                return {
                    "success": True,
                    "analysis_type": "pattern",
                    "pattern_type": "arithmetic" if len(set(differences)) <= 2 else "other",
                    "differences": differences[:10],
                    "constant_difference": all(d == differences[0] for d in differences),
                }
        
        return {"success": True, "analysis_type": "pattern", "patterns_found": []}
    
    def _distribution_analysis(self, data: Any) -> Dict[str, Any]:
        """Analyze distribution of data."""
        
        if not isinstance(data, list):
            return {"error": "Data must be a list", "success": False}
        
        # Count occurrences
        if isinstance(data[0], str):
            from collections import Counter
            counts = Counter(data)
            
            return {
                "success": True,
                "analysis_type": "distribution",
                "unique_values": len(counts),
                "total_items": len(data),
                "top_10": dict(counts.most_common(10)),
            }
        
        return {"success": True, "analysis_type": "distribution"}
