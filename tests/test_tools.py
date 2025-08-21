
# tests/test_tools.py
import pytest
from unittest.mock import Mock, patch
from tools.faa_scraper import FAARegistrationScraper
from tools.flightaware_scraper import FlightAwareScraper
from tools.tavily_search import TavilyOwnershipSearch
from tools.ownership_analyzer import OwnershipAnalyzer

class TestFAARegistrationScraper:
    
    def test_n_number_cleaning(self):
        scraper = FAARegistrationScraper()
        
        # Test with 'N' prefix
        result = scraper._run("N540JT")
        assert "540JT" in str(result)
        
        # Test without 'N' prefix
        result = scraper._run("540JT")
        assert "540JT" in str(result)
    
    @patch('tools.faa_scraper.WebScraper.get_page_content')
    def test_error_handling(self, mock_get_content):
        mock_get_content.return_value = None
        
        scraper = FAARegistrationScraper()
        result = scraper._run("INVALID")
        
        assert "error" in result

class TestFlightAwareScraper:
    
    @patch('tools.flightaware_scraper.WebScraper.get_selenium_driver')
    def test_selenium_setup(self, mock_driver):
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        scraper = FlightAwareScraper()
        result = scraper._run("540JT")
        
        mock_driver.assert_called_once()

class TestOwnershipAnalyzer:
    
    def test_company_type_identification(self):
        analyzer = OwnershipAnalyzer()
        
        # Test LLC identification
        assert analyzer._identify_company_type("ACME Holdings LLC") == "LLC"
        
        # Test Corporation identification
        assert analyzer._identify_company_type("Boeing Corporation") == "Corporation"
        
        # Test individual identification
        assert analyzer._identify_company_type("John Smith") == "Unknown"