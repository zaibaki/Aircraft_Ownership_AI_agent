# tools/faa_scraper.py
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from tools.base import BaseResearchTool
from utils.web_utils import WebScraper
from models.schemas import AircraftRegistration
from pydantic import Field

class FAARegistrationScraper(BaseResearchTool):
    """Tool to scrape FAA aircraft registration data."""
    
    name: str = Field(default="faa_registration_scraper", description="FAA Registration Scraper")
    description: str = Field(default="""
    Scrapes aircraft registration data from the FAA registry.
    Input: n_number (aircraft tail number without 'N' prefix, e.g., '540JT')
    Returns: Detailed aircraft registration information including owner, manufacturer, model, etc.
    """)
    
    def __init__(self):
        super().__init__()
        self.scraper = WebScraper()
        self.base_url = "https://registry.faa.gov/AircraftInquiry/Search/NNumberResult"
    
    def _run(self, n_number: str) -> Dict[str, Any]:
        """Execute the FAA scraping."""
        try:
            self._log_tool_start({"n_number": n_number})
            
            # Clean and validate N-number
            clean_n_number = n_number.upper().replace('N', '').strip()
            if not clean_n_number:
                raise ValueError("Invalid N-number provided")
            
            # Construct URL
            url = f"{self.base_url}?nNumberTxt=N{clean_n_number}"
            
            # Get page content
            content = self.scraper.get_page_content(url)
            if not content:
                return {"error": "Failed to fetch FAA data", "n_number": n_number}
            
            # Parse the content
            result = self._parse_faa_data(content, f"N{clean_n_number}")
            
            self._log_tool_end(result)
            return result
            
        except Exception as e:
            self._log_error(e, {"n_number": n_number})
            return {"error": str(e), "n_number": n_number}
    
    def _parse_faa_data(self, html_content: str, n_number: str) -> Dict[str, Any]:
        """Parse FAA registration data from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            "n_number": n_number,
            "source": "FAA Registry",
            "url": f"{self.base_url}?nNumberTxt={n_number}"
        }
        
        try:
            # Look for data tables or sections
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common field names
                        field_mapping = {
                            'serial number': 'serial_number',
                            'aircraft mfr': 'aircraft_manufacturer',
                            'aircraft model': 'aircraft_model',
                            'aircraft type': 'aircraft_type',
                            'engine mfr': 'engine_manufacturer',
                            'engine model': 'engine_model',
                            'year mfr': 'year_manufactured',
                            'name': 'registrant_name',
                            'street': 'registrant_street',
                            'city': 'registrant_city',
                            'state': 'registrant_state',
                            'zip code': 'registrant_zip',
                            'country': 'registrant_country',
                            'last action date': 'last_activity_date',
                            'cert issue date': 'certificate_issue_date',
                            'airworthiness date': 'airworthiness_date'
                        }
                        
                        for pattern, field in field_mapping.items():
                            if pattern in key:
                                data[field] = value
                                break
            
            # Try to find registrant information in div elements
            registrant_divs = soup.find_all('div', class_=re.compile(r'registrant|owner', re.I))
            for div in registrant_divs:
                text = div.get_text(strip=True)
                if text and 'registrant_name' not in data:
                    data['registrant_name'] = text.split('\n')[0] if '\n' in text else text
            
            self.logger.info(f"Successfully parsed FAA data for {n_number}")
            return data
            
        except Exception as e:
            self.logger.warning(f"Error parsing FAA data: {str(e)}")
            data['parse_error'] = str(e)
            return data