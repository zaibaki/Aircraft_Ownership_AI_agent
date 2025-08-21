# tools/human_assistance.py
from typing import Dict
from langchain_core.tools import tool
from langgraph.types import Command, interrupt
from langsmith import traceable

@tool
@traceable
def human_assistance(
    query: str, 
    research_data: Dict = None, 
    confidence_score: int = 0,
    reason: str = "complex_case"
) -> str:
    """
    Request human assistance for complex aircraft ownership research.
    
    Args:
        query: The research question or issue
        research_data: Current research findings
        confidence_score: Current confidence level
        reason: Reason for human escalation
    
    Returns:
        Human expert guidance
    """
    
    escalation_data = {
        "query": query,
        "research_data": research_data,
        "confidence_score": confidence_score,
        "reason": reason,
        "escalation_type": "aircraft_ownership_research",
        "requires_expertise": True
    }
    
    human_response = interrupt(escalation_data)
    
    return human_response.get("guidance", "No guidance provided")
