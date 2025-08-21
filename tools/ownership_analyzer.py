# tools/ownership_analyzer.py
import re
from typing import Dict, Any, List, Optional
from tools.base import BaseResearchTool
from models.schemas import OwnershipInfo
from pydantic import Field

class OwnershipAnalyzer(BaseResearchTool):
    """Tool to analyze and enhance ownership information from multiple sources."""
    
    name: str = Field(default="ownership_analyzer", description="Ownership Analyzer")
    description: str = Field(default="""
    Analyzes ownership data from multiple sources to identify decision makers and contacts.
    Input: combined_data (dict containing FAA, FlightAware, and search results)
    Returns: Enhanced ownership information with decision maker details and confidence scores.
    """)
    
    def __init__(self):
        super().__init__()
        self.company_types = ['LLC', 'Corporation', 'Inc', 'Corp', 'Limited', 'LP', 'LLP']
        self.executive_titles = ['CEO', 'President', 'Owner', 'Manager', 'Director', 'Principal']
    
    def _run(self, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ownership information."""
        try:
            self._log_tool_start({"data_sources": list(combined_data.keys())})
            
            # Extract information from different sources
            faa_data = combined_data.get('faa_data', {})
            flightaware_data = combined_data.get('flightaware_data', {})
            search_results = combined_data.get('search_results', [])
            
            # Analyze ownership
            ownership_info = self._analyze_ownership(faa_data, flightaware_data, search_results)
            
            self._log_tool_end(ownership_info)
            return ownership_info
            
        except Exception as e:
            self._log_error(e, {"combined_data": str(combined_data)[:200]})
            return {"error": str(e)}
    
    def _analyze_ownership(self, faa_data: Dict, flightaware_data: Dict, 
                          search_results: List[Dict]) -> Dict[str, Any]:
        """Analyze ownership information from multiple sources."""
        
        analysis = {
            "primary_owner": None,
            "decision_maker": None,
            "role": None,
            "email": None,
            "phone": None,
            "linkedin": None,
            "company_type": None,
            "evidence_links": [],
            "identification_method": None,
            "confidence_score": 0.0,
            "analysis_details": []
        }
        
        # Get primary owner from FAA data
        primary_owner = faa_data.get('registrant_name') or flightaware_data.get('owner_name')
        if primary_owner:
            analysis['primary_owner'] = primary_owner
            analysis['analysis_details'].append(f"Primary owner identified: {primary_owner}")
        
        # Determine company type
        if primary_owner:
            company_type = self._identify_company_type(primary_owner)
            if company_type:
                analysis['company_type'] = company_type
                analysis['analysis_details'].append(f"Company type: {company_type}")
        
        # Extract contact information from search results
        contacts = self._extract_contact_info(search_results)
        if contacts:
            analysis.update(contacts)
        
        # Determine decision maker
        decision_maker_info = self._identify_decision_maker(primary_owner, search_results)
        if decision_maker_info:
            analysis.update(decision_maker_info)
        
        # Calculate confidence score
        analysis['confidence_score'] = self._calculate_confidence_score(analysis)
        
        # Set identification method
        analysis['identification_method'] = self._determine_identification_method(analysis)
        
        return analysis
    
    def _identify_company_type(self, owner_name: str) -> Optional[str]:
        """Identify the type of company/entity."""
        if not owner_name:
            return None
        
        owner_upper = owner_name.upper()
        
        for company_type in self.company_types:
            if company_type.upper() in owner_upper:
                return company_type
        
        # Check for individual vs company indicators
        if any(title in owner_upper for title in ['MR.', 'MS.', 'DR.', 'PROF.']):
            return "Individual"
        
        if any(word in owner_upper for word in ['TRUST', 'FOUNDATION', 'ESTATE']):
            return "Trust/Foundation"
        
        return "Unknown"
    
    def _extract_contact_info(self, search_results: List[Dict]) -> Dict[str, Any]:
        """Extract contact information from search results."""
        contacts = {}
        evidence_links = []
        
        for result in search_results:
            if isinstance(result, dict) and 'results' in result:
                for item in result['results']:
                    # Extract emails
                    if 'emails' in item and item['emails']:
                        if not contacts.get('email'):
                            contacts['email'] = item['emails'][0]
                            evidence_links.append(item.get('url', ''))
                    
                    # Extract phones
                    if 'phones' in item and item['phones']:
                        if not contacts.get('phone'):
                            contacts['phone'] = item['phones'][0]
                            evidence_links.append(item.get('url', ''))
                    
                    # Check for LinkedIn
                    if item.get('linkedin_profile') and not contacts.get('linkedin'):
                        contacts['linkedin'] = item.get('url', '')
                        evidence_links.append(item.get('url', ''))
        
        if evidence_links:
            contacts['evidence_links'] = list(set(evidence_links))
        
        return contacts
    
    def _identify_decision_maker(self, primary_owner: str, 
                               search_results: List[Dict]) -> Dict[str, Any]:
        """Identify the likely decision maker."""
        decision_info = {}
        
        if not primary_owner:
            return decision_info
        
        # For individuals, they are likely the decision maker
        if self._identify_company_type(primary_owner) == "Individual":
            decision_info['decision_maker'] = primary_owner
            decision_info['role'] = "Owner"
            return decision_info
        
        # For companies, look for executives in search results
        for result in search_results:
            if isinstance(result, dict) and 'results' in result:
                for item in result['results']:
                    content = item.get('content', '').lower()
                    
                    # Look for executive titles
                    for title in self.executive_titles:
                        if title.lower() in content:
                            # Try to extract the name associated with the title
                            sentences = content.split('.')
                            for sentence in sentences:
                                if title.lower() in sentence:
                                    # Extract potential name (very basic NLP)
                                    words = sentence.split()
                                    title_idx = next((i for i, word in enumerate(words) 
                                                    if title.lower() in word.lower()), -1)
                                    if title_idx != -1:
                                        # Look for capitalized words nearby (potential names)
                                        for i in range(max(0, title_idx-3), min(len(words), title_idx+4)):
                                            word = words[i].strip(',').strip()
                                            if (word.istitle() and len(word) > 2 and 
                                                word not in ['The', 'And', 'Of', 'For']):
                                                decision_info['decision_maker'] = word
                                                decision_info['role'] = title
                                                return decision_info
        
        # Default for companies - assume primary contact
        if self._identify_company_type(primary_owner) in ['LLC', 'Corporation', 'Inc']:
            decision_info['decision_maker'] = f"{primary_owner} (Primary Contact)"
            decision_info['role'] = "Company Representative"
        
        return decision_info
    
    def _calculate_confidence_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on available information."""
        score = 0.0
        
        # Base score for having primary owner
        if analysis.get('primary_owner'):
            score += 0.3
        
        # Points for contact information
        if analysis.get('email'):
            score += 0.2
        if analysis.get('phone'):
            score += 0.2
        if analysis.get('linkedin'):
            score += 0.1
        
        # Points for identified decision maker
        if analysis.get('decision_maker'):
            score += 0.1
        
        # Points for evidence links
        if analysis.get('evidence_links'):
            score += min(0.1, len(analysis['evidence_links']) * 0.02)
        
        return min(1.0, score)
    
    def _determine_identification_method(self, analysis: Dict[str, Any]) -> str:
        """Determine how the ownership was identified."""
        methods = []
        
        if analysis.get('primary_owner'):
            methods.append("FAA Registry")
        
        if analysis.get('email') or analysis.get('phone'):
            methods.append("Web Search")
        
        if analysis.get('linkedin'):
            methods.append("LinkedIn Profile")
        
        if analysis.get('company_type'):
            methods.append("Business Entity Analysis")
        
        return " + ".join(methods) if methods else "Limited Information"