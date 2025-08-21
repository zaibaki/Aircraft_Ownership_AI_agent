#!/usr/bin/env python3
"""
Fixed FAA tools with proper tool calling and logging
"""

import csv
import zipfile
import requests
from pathlib import Path
from typing import Dict, List, Optional
from langchain_core.tools import tool
from bs4 import BeautifulSoup
import pandas as pd
import logging
from io import BytesIO

from config.settings import FAA_DB_DIR, FAA_DOWNLOAD_URL, FAA_BASE_URL, CACHE_DIR
from utils.logging_config import track_tool_execution
from config.langsmith_config import traceable

logger = logging.getLogger(__name__)

class FAATools:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @track_tool_execution("faa_database_download")
    def download_faa_database(self) -> bool:
        """Download and extract FAA database files"""
        try:
            logger.info("Starting FAA database download...")
            response = self.session.get(FAA_DOWNLOAD_URL, stream=True, timeout=60)
            response.raise_for_status()
            
            logger.info("Extracting FAA database files...")
            with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                zip_file.extractall(FAA_DB_DIR)
            
            logger.info("FAA database downloaded and extracted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading FAA database: {e}")
            return False
    
    @track_tool_execution("faa_master_load")
    def load_master_database(self) -> pd.DataFrame:
        """Load the FAA MASTER.txt file into pandas DataFrame"""
        master_file = FAA_DB_DIR / "MASTER.txt"
        
        if not master_file.exists():
            logger.warning("MASTER.txt not found, attempting download...")
            if not self.download_faa_database():
                raise FileNotFoundError("Could not download FAA database")
        
        try:
            logger.info("Loading FAA master database...")
            df = pd.read_csv(
                master_file,
                dtype=str,  # Keep everything as string to preserve leading zeros
                na_filter=False,  # Don't convert empty strings to NaN
                low_memory=False
            )
            logger.info(f"Loaded {len(df)} aircraft records from FAA database")
            return df
        except Exception as e:
            logger.error(f"Error loading FAA master database: {e}")
            return pd.DataFrame()

@tool
@traceable
def faa_database_lookup(n_number: str) -> Dict:
    """
    Look up aircraft in local FAA master database.
    
    Args:
        n_number: Aircraft N-number (e.g., "N123AB")
    
    Returns:
        Dictionary with aircraft registration details
    """
    logger.info(f"FAA database lookup initiated for {n_number}")
    
    faa_tools = FAATools()
    clean_n_number = n_number.upper().replace('N', '').strip()
    
    try:
        df = faa_tools.load_master_database()
        
        if df.empty:
            logger.error("FAA database is empty or failed to load")
            return {"error": "FAA database not available", "tool": "faa_database_lookup"}
        
        # Search for the aircraft
        aircraft_records = df[df['N-NUMBER'].str.strip() == clean_n_number]
        
        if aircraft_records.empty:
            logger.warning(f"Aircraft N{clean_n_number} not found in FAA database")
            return {"error": f"Aircraft N{clean_n_number} not found in FAA database", "tool": "faa_database_lookup"}
        
        # Get the first (most recent) record
        record = aircraft_records.iloc[0]
        
        result = {
            "tool": "faa_database_lookup",
            "n_number": f"N{clean_n_number}",
            "serial_number": record.get('SERIAL NUMBER', '').strip(),
            "manufacturer_model": record.get('MFR MDL CODE', '').strip(),
            "year_manufactured": record.get('YEAR MFR', '').strip(),
            "registration_type": record.get('TYPE REGISTRANT', '').strip(),
            "owner_name": record.get('NAME', '').strip(),
            "street": record.get('STREET', '').strip(),
            "street2": record.get('STREET2', '').strip(),
            "city": record.get('CITY', '').strip(),
            "state": record.get('STATE', '').strip(),
            "zip_code": record.get('ZIP CODE', '').strip(),
            "country": record.get('COUNTRY', '').strip(),
            "aircraft_type": record.get('TYPE AIRCRAFT', '').strip(),
            "engine_type": record.get('TYPE ENGINE', '').strip(),
            "status_code": record.get('STATUS CODE', '').strip(),
            "certification_date": record.get('CERT ISSUE DATE', '').strip(),
            "airworthiness_date": record.get('AIR WORTH DATE', '').strip(),
            "expiration_date": record.get('EXPIRATION DATE', '').strip(),
            "mode_s_code": record.get('MODE S CODE HEX', '').strip(),
            "source": "faa_database",
            "lookup_timestamp": pd.Timestamp.now().isoformat()
        }
        
        logger.info(f"Successfully found aircraft N{clean_n_number} in FAA database")
        return result
        
    except Exception as e:
        logger.error(f"Database lookup failed for {n_number}: {str(e)}")
        return {"error": f"Database lookup failed: {str(e)}", "tool": "faa_database_lookup"}

@tool
@traceable
def faa_web_scraper(n_number: str) -> Dict:
    """
    Scrape current FAA registry website for aircraft data.
    
    Args:
        n_number: Aircraft N-number (e.g., "N123AB")
    
    Returns:
        Dictionary with current aircraft registration details
    """
    logger.info(f"FAA web scraper initiated for {n_number}")
    
    faa_tools = FAATools()
    clean_n_number = n_number.upper().replace('N', '').strip()
    
    try:
        url = f"{FAA_BASE_URL}/AircraftInquiry/Search/NNumberResult"
        params = {'nNumberTxt': clean_n_number}
        
        logger.info(f"Fetching data from FAA website for N{clean_n_number}")
        response = faa_tools.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if aircraft found
        if "aircraft was not found" in response.text.lower():
            logger.warning(f"Aircraft N{clean_n_number} not found on FAA website")
            return {"error": f"Aircraft N{clean_n_number} not found in FAA registry", "tool": "faa_web_scraper"}
        
        # Extract data from tables
        aircraft_data = {
            "tool": "faa_web_scraper",
            "n_number": f"N{clean_n_number}",
            "source": "faa_web_scraper",
            "lookup_timestamp": pd.Timestamp.now().isoformat(),
            "registry_url": f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        }
        
        # Parse tables for structured data
        tables = soup.find_all('table', class_='devkit-table')
        logger.info(f"Found {len(tables)} tables to parse on FAA website")
        
        for table in tables:
            caption = table.find('caption')
            if not caption:
                continue
                
            caption_text = caption.get_text().strip().lower()
            
            if 'aircraft description' in caption_text:
                logger.debug("Parsing aircraft description table")
                aircraft_data.update(_parse_aircraft_description_table(table))
            elif 'registered owner' in caption_text:
                logger.debug("Parsing registered owner table")
                aircraft_data.update(_parse_owner_table(table))
            elif 'airworthiness' in caption_text:
                logger.debug("Parsing airworthiness table")
                aircraft_data.update(_parse_airworthiness_table(table))
        
        logger.info(f"Successfully scraped data for N{clean_n_number} from FAA website")
        return aircraft_data
        
    except Exception as e:
        logger.error(f"Web scraping failed for {n_number}: {str(e)}")
        return {"error": f"Web scraping failed: {str(e)}", "tool": "faa_web_scraper"}

def _parse_aircraft_description_table(table) -> Dict:
    """Parse aircraft description table from FAA website"""
    data = {}
    rows = table.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            for i in range(0, len(cells), 2):
                if i + 1 < len(cells):
                    key = cells[i].get_text().strip().lower()
                    value = cells[i + 1].get_text().strip()
                    
                    if 'serial number' in key:
                        data['serial_number'] = value
                    elif 'manufacturer name' in key:
                        data['manufacturer'] = value
                    elif 'model' in key:
                        data['model'] = value
                    elif 'mfr year' in key:
                        data['year_manufactured'] = value
                    elif 'type aircraft' in key:
                        data['aircraft_type'] = value
                    elif 'type engine' in key:
                        data['engine_type'] = value
                    elif 'certificate issue date' in key:
                        data['certificate_issue_date'] = value
                    elif 'status' in key:
                        data['status'] = value
    
    return data

def _parse_owner_table(table) -> Dict:
    """Parse registered owner table from FAA website"""
    data = {}
    rows = table.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            key = cells[0].get_text().strip().lower()
            value = cells[-1].get_text().strip()  # Take last cell for multi-column rows
            
            if 'name' in key:
                data['owner_name'] = value
            elif 'street' in key:
                data['street'] = value
            elif 'city' in key:
                data['city'] = value
            elif 'state' in key:
                data['state'] = value
            elif 'zip code' in key:
                data['zip_code'] = value
            elif 'country' in key:
                data['country'] = value
            elif 'county' in key:
                data['county'] = value
    
    return data

def _parse_airworthiness_table(table) -> Dict:
    """Parse airworthiness table from FAA website"""
    data = {}
    rows = table.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            for i in range(0, len(cells), 2):
                if i + 1 < len(cells):
                    key = cells[i].get_text().strip().lower()
                    value = cells[i + 1].get_text().strip()
                    
                    if 'a/w date' in key or 'airworthiness date' in key:
                        data['airworthiness_date'] = value
                    elif 'engine manufacturer' in key:
                        data['engine_manufacturer'] = value
                    elif 'engine model' in key:
                        data['engine_model'] = value
                    elif 'classification' in key:
                        data['classification'] = value
    
    return data