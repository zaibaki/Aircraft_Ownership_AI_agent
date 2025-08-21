
# utils/web_utils.py
import requests
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import logging

logger = logging.getLogger("aircraft_research.web_utils")

class WebScraper:
    """Base web scraper with common functionality."""
    
    def __init__(self, timeout: int = 30, headless: bool = True):
        self.timeout = timeout
        self.headless = headless
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get page content using requests."""
        try:
            logger.info(f"Fetching content from: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Successfully fetched content from: {url}")
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def get_selenium_driver(self) -> webdriver.Chrome:
        """Create and return a Selenium Chrome driver."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.timeout)
        return driver
    
    def wait_for_element(self, driver: webdriver.Chrome, selector: str, 
                        by: By = By.CSS_SELECTOR, timeout: int = 10):
        """Wait for an element to be present."""
        try:
            wait = WebDriverWait(driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except Exception as e:
            logger.warning(f"Element not found: {selector} - {str(e)}")
            return None
