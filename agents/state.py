# agents/state.py
from typing import Annotated, List, Dict, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AircraftResearchState(TypedDict):
    # Core input
    query: str  # N-number or make/model
    
    # Messages for conversation flow
    messages: Annotated[list, add_messages]
    
    # Aircraft data
    aircraft_info: Optional[Dict]
    faa_registration: Optional[Dict]
    
    # Ownership analysis
    owner_analysis: Optional[Dict]
    corporate_entities: List[Dict]
    ownership_chain: List[Dict]
    
    # Contact information
    decision_makers: List[Dict]
    primary_contact: Optional[Dict]
    
    # Operational data
    flight_patterns: Optional[Dict]
    base_airports: List[str]
    
    # Analysis results
    confidence_score: int
    confidence_justification: str
    evidence_links: List[Dict]
    recommendations: List[str]
    
    # Control flow
    needs_human_review: bool
    research_status: str  # "started", "gathering", "analyzing", "complete", "failed"
