# tools/corporate_tools.py
import requests
from typing import Dict, List
from langchain_core.tools import tool
from langsmith import traceable
from bs4 import BeautifulSoup

from config.settings import OPENCORPORATES_BASE_URL

class CorporateTools:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AircraftOwnershipResearch/1.0'
        })

@tool
@traceable
def opencorporates_search(company_name: str, jurisdiction: str = "us") -> List[Dict]:
    """
    Search OpenCorporates for company information using reconciliation API.
    
    Args:
        company_name: Name of company to search
        jurisdiction: Jurisdiction code (default: "us")
    
    Returns:
        List of company matches with details
    """
    corporate_tools = CorporateTools()
    
    try:
        url = f"{OPENCORPORATES_BASE_URL}/{jurisdiction}"
        params = {
            'query': company_name,
            'limit': 5
        }
        
        response = corporate_tools.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('result', [])
        
        companies = []
        for result in results:
            company = {
                'id': result.get('id'),
                'name': result.get('name'),
                'score': result.get('score', 0),
                'match': result.get('match', False),
                'opencorporates_url': result.get('uri'),
                'source': 'opencorporates_reconcile'
            }
            
            # Get detailed information if available
            if company['id']:
                details = _get_company_details(corporate_tools, company['id'])
                if details:
                    company.update(details)
            
            companies.append(company)
        
        return companies
        
    except Exception as e:
        return [{"error": f"OpenCorporates search failed: {str(e)}"}]

def _get_company_details(corporate_tools: CorporateTools, company_id: str) -> Dict:
    """Get detailed company information using flyout endpoint"""
    try:
        url = f"{OPENCORPORATES_BASE_URL}/flyout"
        params = {'id': company_id}
        
        response = corporate_tools.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        html_content = data.get('html', '')
        
        if not html_content or "No company found" in html_content:
            return {}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        details = {}
        
        # Extract company name
        title_elem = soup.find('h1', {'id': 'oc-flyout-title'})
        if title_elem:
            details['full_name'] = title_elem.get_text().strip()
        
        # Extract properties
        property_elems = soup.find_all('h3', class_='oc-topic-properties')
        for prop in property_elems:
            text = prop.get_text().strip()
            
            if 'Status:' in text:
                details['status'] = text.split('Status:')[1].strip()
            elif 'Company No:' in text:
                details['company_number'] = text.split('Company No:')[1].strip()
            elif 'Registered:' in text:
                details['incorporation_date'] = text.split('Registered:')[1].strip()
            elif 'Address:' in text:
                details['address'] = text.split('Address:')[1].strip()
        
        # Extract jurisdiction info
        attribution = soup.find('div', class_='oc-attribution')
        if attribution:
            jurisdiction_text = attribution.get_text().strip()
            if ' - ' in jurisdiction_text:
                parts = jurisdiction_text.split(' - ')
                if len(parts) >= 2:
                    details['jurisdiction'] = parts[0].strip()
                    details['company_type'] = parts[1].strip()
        
        return details
        
    except Exception as e:
        return {"error": f"Failed to get company details: {str(e)}"}

@tool
@traceable
def bizapedia_search(company_name: str, state: str = None) -> Dict:
    """
    Search Bizapedia for company information (web scraping).
    
    Args:
        company_name: Name of company to search
        state: State abbreviation to narrow search
    
    Returns:
        Company information from Bizapedia
    """
    # Note: Bizapedia doesn't have a public API, so this would require web scraping
    # For now, return a placeholder that indicates the need for web scraping
    return {
        "message": "Bizapedia search requires web scraping implementation",
        "company_name": company_name,
        "state": state,
        "source": "bizapedia_placeholder"
    }
