# agents/nodes.py
from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import traceable

from typing import List

from agents.state import AircraftResearchState
from tools.faa_tools import faa_database_lookup, faa_web_scraper
from tools.corporate_tools import opencorporates_search
from tools.contact_tools import contact_enrichment
from tools.flight_tools import flight_pattern_analysis
from tools.human_assistance import human_assistance
from config.prompts import CONFIDENCE_SCORING_PROMPT

@traceable
def research_coordinator(state: AircraftResearchState) -> AircraftResearchState:
    """
    Coordinate the research process and determine next steps.
    """
    query = state["query"]
    
    # Update status
    state["research_status"] = "started"
    state["messages"].append(
        AIMessage(content=f"Starting aircraft ownership research for: {query}")
    )
    
    # Determine if this is an N-number or make/model search
    if query.upper().startswith('N') and len(query) <= 8:
        # This is likely an N-number
        state["research_status"] = "gathering"
        return state
    else:
        # This might be a make/model search - would need different approach
        state["messages"].append(
            AIMessage(content="Make/model search not yet implemented. Please provide an N-number.")
        )
        state["research_status"] = "failed"
        return state

@traceable
def aircraft_data_gatherer(state: AircraftResearchState) -> AircraftResearchState:
    """
    Gather aircraft data from FAA sources.
    """
    query = state["query"]
    
    # Try database lookup first
    db_result = faa_database_lookup.invoke({"n_number": query})
    
    # Try web scraping as backup/verification
    web_result = faa_web_scraper.invoke({"n_number": query})
    
    # Combine results
    aircraft_info = {}
    if not db_result.get("error"):
        aircraft_info.update(db_result)
        aircraft_info["database_lookup"] = "success"
    
    if not web_result.get("error"):
        aircraft_info.update(web_result)
        aircraft_info["web_scraping"] = "success"
    
    if not aircraft_info:
        state["messages"].append(
            AIMessage(content=f"Aircraft {query} not found in FAA records")
        )
        state["research_status"] = "failed"
        return state
    
    state["aircraft_info"] = aircraft_info
    state["faa_registration"] = aircraft_info
    
    state["messages"].append(
        AIMessage(content=f"Found aircraft data for {aircraft_info.get('n_number', query)}")
    )
    
    return state

@traceable
def ownership_analyzer(state: AircraftResearchState) -> AircraftResearchState:
    """
    Analyze ownership structure and identify corporate entities.
    """
    aircraft_info = state.get("aircraft_info", {})
    owner_name = aircraft_info.get("owner_name", "")
    
    if not owner_name:
        state["messages"].append(
            AIMessage(content="No owner information found to analyze")
        )
        return state
    
    # Classify owner type
    owner_analysis = _classify_owner_type(owner_name)
    state["owner_analysis"] = owner_analysis
    
    # If it's a business entity, search corporate records
    corporate_entities = []
    if owner_analysis.get("is_business"):
        search_terms = owner_analysis.get("search_terms", [owner_name])
        
        for term in search_terms[:2]:  # Limit searches
            results = opencorporates_search.invoke({
                "company_name": term,
                "jurisdiction": "us"
            })
            
            if isinstance(results, list):
                corporate_entities.extend(results)
    
    state["corporate_entities"] = corporate_entities
    
    state["messages"].append(
        AIMessage(content=f"Analyzed ownership: {owner_analysis.get('entity_type', 'Unknown')} - Found {len(corporate_entities)} corporate matches")
    )
    
    return state

@traceable
def contact_researcher(state: AircraftResearchState) -> AircraftResearchState:
    """
    Research contact information for decision makers.
    """
    corporate_entities = state.get("corporate_entities", [])
    decision_makers = []
    
    # Extract potential decision makers from corporate entities
    for entity in corporate_entities:
        if entity.get("score", 0) > 60:  # Only high-confidence matches
            # Try to enrich contact information
            contact_result = contact_enrichment.invoke({
                "name": entity.get("name", ""),
                "company": entity.get("name", ""),
                "domain": _extract_domain_from_company(entity.get("name", ""))
            })
            
            if contact_result:
                decision_makers.append(contact_result)
    
    state["decision_makers"] = decision_makers
    
    # Select primary contact (highest confidence)
    if decision_makers:
        primary = max(decision_makers, key=lambda x: x.get("confidence", 0))
        state["primary_contact"] = primary
    
    state["messages"].append(
        AIMessage(content=f"Researched contacts: {len(decision_makers)} potential decision makers found")
    )
    
    return state

@traceable
def confidence_assessor(state: AircraftResearchState) -> AircraftResearchState:
    """
    Calculate confidence score and generate recommendations.
    """
    # Calculate confidence based on available data
    confidence_score = 0
    justification_parts = []
    
    # Aircraft data quality (30 points max)
    if state.get("aircraft_info"):
        confidence_score += 20
        justification_parts.append("Aircraft found in FAA records (+20)")
        
        if state["aircraft_info"].get("owner_name"):
            confidence_score += 10
            justification_parts.append("Owner information available (+10)")
    
    # Corporate entity matches (25 points max)
    corporate_entities = state.get("corporate_entities", [])
    if corporate_entities:
        high_score_entities = [e for e in corporate_entities if e.get("score", 0) > 70]
        if high_score_entities:
            confidence_score += 20
            justification_parts.append(f"High-confidence corporate matches found (+20)")
        elif len(corporate_entities) > 0:
            confidence_score += 10
            justification_parts.append("Corporate entities found but low confidence (+10)")
    
    # Contact information quality (25 points max)
    decision_makers = state.get("decision_makers", [])
    if decision_makers:
        if state.get("primary_contact", {}).get("confidence", 0) > 70:
            confidence_score += 20
            justification_parts.append("High-confidence contact information (+20)")
        else:
            confidence_score += 10
            justification_parts.append("Contact information found but needs verification (+10)")
    
    # Owner analysis quality (20 points max)
    owner_analysis = state.get("owner_analysis", {})
    if owner_analysis.get("entity_type") != "Individual/Unknown":
        confidence_score += 15
        justification_parts.append("Clear entity type identified (+15)")
    
    # Cap at 100
    confidence_score = min(confidence_score, 100)
    
    # Generate justification
    justification = "Confidence Assessment: " + "; ".join(justification_parts)
    if confidence_score < 50:
        justification += ". Requires additional research or human review."
    
    state["confidence_score"] = confidence_score
    state["confidence_justification"] = justification
    
    # Generate recommendations
    recommendations = _generate_recommendations(state, confidence_score)
    state["recommendations"] = recommendations
    
    # Determine if human review is needed
    state["needs_human_review"] = confidence_score < 40 or len(corporate_entities) == 0
    
    state["messages"].append(
        AIMessage(content=f"Confidence Assessment Complete: {confidence_score}% - {justification}")
    )
    
    return state

def _classify_owner_type(owner_name: str) -> Dict:
    """Classify owner as individual or business entity"""
    business_indicators = [
        'LLC', 'INC', 'CORP', 'CORPORATION', 'COMPANY', 'CO', 'LTD', 'LIMITED',
        'TRUST', 'TRUSTEE', 'PARTNERSHIP', 'LP', 'LLP', 'HOLDINGS', 'GROUP',
        'AVIATION', 'AIRCRAFT', 'JETS', 'FLYING', 'CHARTER', 'MANAGEMENT',
        'ENTERPRISES', 'SERVICES', 'SOLUTIONS', 'VENTURES'
    ]
    
    name_upper = owner_name.upper()
    is_business = any(indicator in name_upper for indicator in business_indicators)
    
    # Generate search terms
    search_terms = [owner_name]
    if is_business:
        # Clean name for better searching
        clean_name = owner_name
        for suffix in [' LLC', ' INC', ' CORP', ' LTD', ' CO']:
            if clean_name.upper().endswith(suffix):
                clean_name = clean_name[:-len(suffix)].strip()
                search_terms.append(clean_name)
    
    entity_type = "Individual/Unknown"
    if 'TRUST' in name_upper:
        entity_type = "Trust"
    elif any(x in name_upper for x in ['LLC', 'LIMITED LIABILITY']):
        entity_type = "Limited Liability Company"
    elif any(x in name_upper for x in ['INC', 'CORP', 'CORPORATION']):
        entity_type = "Corporation"
    elif any(x in name_upper for x in ['LP', 'LLP', 'PARTNERSHIP']):
        entity_type = "Partnership"
    
    return {
        "original_name": owner_name,
        "is_business": is_business,
        "entity_type": entity_type,
        "search_terms": search_terms
    }

def _extract_domain_from_company(company_name: str) -> str:
    """Extract likely domain from company name"""
    if not company_name:
        return ""
    
    # Simple domain generation - in real implementation would use domain discovery APIs
    clean_name = company_name.lower()
    for suffix in [' llc', ' inc', ' corp', ' ltd', ' co']:
        clean_name = clean_name.replace(suffix, '')
    
    # Remove special characters and spaces
    clean_name = ''.join(c for c in clean_name if c.isalnum())
    
    return f"{clean_name}.com"

def _generate_recommendations(state: AircraftResearchState, confidence_score: int) -> List[str]:
    """Generate actionable recommendations based on research findings"""
    recommendations = []
    
    if confidence_score < 40:
        recommendations.append("PRIORITY: Requires human expert review - insufficient data for reliable identification")
    
    owner_analysis = state.get("owner_analysis", {})
    if owner_analysis.get("entity_type") == "Trust":
        recommendations.append("Trust structure detected - beneficial owners may not be publicly available")
    
    corporate_entities = state.get("corporate_entities", [])
    if not corporate_entities and owner_analysis.get("is_business"):
        recommendations.append("Business entity found but no corporate records - check state registries manually")
    
    if len(corporate_entities) > 3:
        recommendations.append("Multiple corporate matches - verify correct entity using address matching")
    
    decision_makers = state.get("decision_makers", [])
    if not decision_makers:
        recommendations.append("No contact information found - may require LinkedIn research or industry networking")
    
    aircraft_info = state.get("aircraft_info", {})
    if aircraft_info.get("status", "").upper() not in ["VALID", "ACTIVE"]:
        recommendations.append("Aircraft registration status requires verification")
    
    return recommendations
