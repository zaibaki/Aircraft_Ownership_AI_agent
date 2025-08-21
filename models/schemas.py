# models/schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AircraftRegistration(BaseModel):
    """Model for FAA aircraft registration data."""
    n_number: str
    serial_number: Optional[str] = None
    aircraft_manufacturer: Optional[str] = None
    aircraft_model: Optional[str] = None
    aircraft_type: Optional[str] = None
    engine_manufacturer: Optional[str] = None
    engine_model: Optional[str] = None
    year_manufactured: Optional[str] = None
    registrant_name: Optional[str] = None
    registrant_street: Optional[str] = None
    registrant_city: Optional[str] = None
    registrant_state: Optional[str] = None
    registrant_zip: Optional[str] = None
    registrant_country: Optional[str] = None
    last_activity_date: Optional[str] = None
    certificate_issue_date: Optional[str] = None
    airworthiness_date: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class FlightAwareData(BaseModel):
    """Model for FlightAware aircraft data."""
    n_number: str
    owner_name: Optional[str] = None
    owner_location: Optional[str] = None
    aircraft_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    base_airport: Optional[str] = None
    registration_date: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class OwnershipInfo(BaseModel):
    """Enhanced ownership information."""
    primary_owner: Optional[str] = None
    decision_maker: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    company_type: Optional[str] = None  # LLC, Corporation, Individual, etc.
    evidence_links: List[str] = []
    identification_method: Optional[str] = None
    confidence_score: Optional[float] = None

class AircraftResearchResult(BaseModel):
    """Complete aircraft research result."""
    n_number: str
    faa_data: Optional[AircraftRegistration] = None
    flightaware_data: Optional[FlightAwareData] = None
    ownership_info: Optional[OwnershipInfo] = None
    additional_findings: List[Dict[str, Any]] = []
    research_timestamp: datetime = datetime.now()
    status: str = "completed"
    errors: List[str] = []

class AgentState(BaseModel):
    """State for the LangGraph agent."""
    n_number: str
    messages: List[Dict[str, Any]] = []
    faa_data: Optional[AircraftRegistration] = None
    flightaware_data: Optional[FlightAwareData] = None
    ownership_info: Optional[OwnershipInfo] = None
    search_results: List[Dict[str, Any]] = []
    final_result: Optional[AircraftResearchResult] = None
    step: str = "init"
