# tools/flightaware_scraper.py
import time
import re
from typing import Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tools.base import BaseResearchTool
from utils.web_utils import WebScraper
from models.schemas import FlightAwareData
from pydantic import Field

class FlightAwareScraper(BaseResearchTool):
    """Tool to scrape FlightAware aircraft data."""
    
    name: str = Field(default="flightaware_scraper", description="FlightAware Scraper")
    description: str = Field(default="""
    Scrapes aircraft data from FlightAware including owner information and base airport.
    Input: n_number (aircraft tail number without 'N' prefix, e.g., '540JT')
    Returns: Aircraft ownership and operational data from FlightAware.
    """)
    
    def __init__(self):
        super().__init__()
        self.scraper = WebScraper()
        self.base_url = "https://www.flightaware.com/resources/registration"
    
    def _run(self, n_number: str) -> Dict[str, Any]:
        """Execute the FlightAware scraping."""
        try:
            self._log_tool_start({"n_number": n_number})
            
            # Clean and validate N-number
            clean_n_number = n_number.upper().replace('N', '').strip()
            if not clean_n_number:
                raise ValueError("Invalid N-number provided")
            
            # Use Selenium for dynamic content
            driver = self.scraper.get_selenium_driver()
            
            try:
                url = f"{self.base_url}/N{clean_n_number}"
                self.logger.info(f"Loading FlightAware page: {url}")
                
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Additional wait for dynamic content
                time.sleep(5)
                
                # Parse the loaded content
                result = self._parse_flightaware_data(driver, f"N{clean_n_number}")
                
                self._log_tool_end(result)
                return result
                
            finally:
                driver.quit()
                
        except Exception as e:
            self._log_error(e, {"n_number": n_number})
            return {"error": str(e), "n_number": n_number}
    
    def _parse_flightaware_data(self, driver, n_number: str) -> Dict[str, Any]:
        """Parse FlightAware data from the loaded page using multiple strategies."""
        data = {
            "n_number": n_number,
            "source": "FlightAware",
            "url": f"{self.base_url}/{n_number}"
        }
        
        try:
            # Strategy 1: Look for page title which often contains aircraft info
            try:
                title = driver.title
                self.logger.info(f"Page title: {title}")
                
                # Extract info from title like "N540W (2024 GULFSTREAM AEROSPACE CORP GVIII-G700 owned by WILMINGTON TRUST CO TRUSTEE)"
                if "owned by" in title:
                    title_match = re.search(r'\((.*?)\s+owned by\s+(.*?)\)', title)
                    if title_match:
                        aircraft_info = title_match.group(1).strip()
                        owner_info = title_match.group(2).strip()
                        
                        data['aircraft_info'] = aircraft_info
                        data['owner_name'] = owner_info
                        
                        # Try to parse aircraft info further
                        aircraft_parts = aircraft_info.split()
                        if len(aircraft_parts) >= 3:
                            data['year_manufactured'] = aircraft_parts[0] if aircraft_parts[0].isdigit() else None
                            data['manufacturer'] = aircraft_parts[1] if len(aircraft_parts) > 1 else None
                            data['model'] = ' '.join(aircraft_parts[2:]) if len(aircraft_parts) > 2 else None
                        
                        self.logger.info(f"Extracted from title - Aircraft: {aircraft_info}, Owner: {owner_info}")
                
            except Exception as e:
                self.logger.warning(f"Could not parse title: {str(e)}")
            
            # Strategy 2: Look for specific content in the page body
            try:
                page_source = driver.page_source
                
                # Look for registration information patterns
                registration_patterns = [
                    r'Registration:\s*([^<\n]+)',
                    r'Owner:\s*([^<\n]+)',
                    r'Registered to:\s*([^<\n]+)',
                    r'Aircraft type:\s*([^<\n]+)',
                    r'Manufacturer:\s*([^<\n]+)',
                    r'Model:\s*([^<\n]+)'
                ]
                
                for pattern in registration_patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        self.logger.info(f"Found pattern {pattern}: {matches}")
                
                # Look for owner information in various formats
                owner_patterns = [
                    r'owned by\s+([^)(<\n]+)',
                    r'Registered to:?\s*([^<\n]+)',
                    r'Owner:?\s*([^<\n]+)'
                ]
                
                for pattern in owner_patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches and not data.get('owner_name'):
                        potential_owner = matches[0].strip()
                        if len(potential_owner) > 3:  # Basic validation
                            data['owner_name'] = potential_owner
                            self.logger.info(f"Found owner via pattern: {potential_owner}")
                            break
            
            except Exception as e:
                self.logger.warning(f"Error in pattern matching: {str(e)}")
            
            # Strategy 3: Look for structured data in tables or lists
            try:
                # Find all text content and look for key-value pairs
                all_text = driver.find_element(By.TAG_NAME, "body").text
                lines = all_text.split('\n')
                
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    
                    # Look for owner information
                    if any(keyword in line_lower for keyword in ['owner:', 'registered to:', 'operated by:']):
                        if i + 1 < len(lines):
                            potential_owner = lines[i + 1].strip()
                            if potential_owner and len(potential_owner) > 3 and not data.get('owner_name'):
                                data['owner_name'] = potential_owner
                                self.logger.info(f"Found owner in structured text: {potential_owner}")
                    
                    # Look for aircraft type/model
                    if any(keyword in line_lower for keyword in ['aircraft type:', 'model:', 'type:']):
                        if i + 1 < len(lines):
                            potential_type = lines[i + 1].strip()
                            if potential_type and len(potential_type) > 2 and not data.get('aircraft_type'):
                                data['aircraft_type'] = potential_type
                                self.logger.info(f"Found aircraft type: {potential_type}")
                    
                    # Look for base airport
                    if any(keyword in line_lower for keyword in ['base:', 'home base:', 'based at:']):
                        if i + 1 < len(lines):
                            potential_base = lines[i + 1].strip()
                            if potential_base and len(potential_base) > 2 and not data.get('base_airport'):
                                data['base_airport'] = potential_base
                                self.logger.info(f"Found base airport: {potential_base}")
            
            except Exception as e:
                self.logger.warning(f"Error in structured text parsing: {str(e)}")
            
            # Strategy 4: Look for meta tags or JSON-LD data
            try:
                meta_tags = driver.find_elements(By.TAG_NAME, "meta")
                for meta in meta_tags:
                    name = meta.get_attribute("name") or meta.get_attribute("property")
                    content = meta.get_attribute("content")
                    
                    if name and content:
                        if "description" in name.lower() and not data.get('meta_description'):
                            data['meta_description'] = content
                            # Try to extract owner from description
                            if "owned by" in content.lower():
                                owner_match = re.search(r'owned by\s+([^)(<\n]+)', content, re.IGNORECASE)
                                if owner_match and not data.get('owner_name'):
                                    data['owner_name'] = owner_match.group(1).strip()
                                    self.logger.info(f"Found owner in meta description: {data['owner_name']}")
                        
                        elif "title" in name.lower() and not data.get('meta_title'):
                            data['meta_title'] = content
            
            except Exception as e:
                self.logger.warning(f"Error parsing meta tags: {str(e)}")
            
            # Strategy 5: Check for "Unknown Aircraft" or error states
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                if "unknown aircraft" in body_text:
                    data['status'] = 'unknown_aircraft'
                    self.logger.info(f"Aircraft {n_number} marked as unknown on FlightAware")
                elif "not found" in body_text or "error" in body_text:
                    data['status'] = 'not_found'
                    self.logger.info(f"Aircraft {n_number} not found on FlightAware")
                else:
                    data['status'] = 'found'
            
            except Exception as e:
                self.logger.warning(f"Error checking aircraft status: {str(e)}")
            
            # Final validation and cleanup
            if data.get('owner_name'):
                # Clean up owner name
                owner = data['owner_name']
                # Remove common prefixes/suffixes that might be artifacts
                owner = re.sub(r'^(owned by|registered to|operator:?)\s*', '', owner, flags=re.IGNORECASE)
                owner = re.sub(r'\s+(aircraft|registration|info).*$', '', owner, flags=re.IGNORECASE)
                data['owner_name'] = owner.strip()
            
            self.logger.info(f"Successfully parsed FlightAware data for {n_number}")
            self.logger.info(f"Data extracted: {list(data.keys())}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing FlightAware data: {str(e)}")
            data['parse_error'] = str(e)
            return data