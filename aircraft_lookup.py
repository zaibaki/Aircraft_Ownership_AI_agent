#!/usr/bin/env python3
"""
Aircraft Ownership & Corporate Research Tool v2
Using current FAA endpoints and OpenCorporates Reconciliation API

Usage:
    python aircraft_lookup.py N12345
    python aircraft_lookup.py --batch aircraft_list.txt
"""

import requests
import json
import re
import time
import argparse
import logging
from typing import Dict, List, Optional
from urllib.parse import quote, urlencode
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FAAAircraftLookup:
    """Handles FAA aircraft registry searches using current endpoints"""
    
    BASE_URL = "https://registry.faa.gov"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def lookup_aircraft(self, n_number: str) -> Optional[Dict]:
        """Lookup aircraft via current FAA registry"""
        clean_n_number = n_number.upper().replace('N', '')
        
        # Try the current working endpoint
        url = f"{self.BASE_URL}/AircraftInquiry/Search/NNumberResult"
        params = {'nNumberTxt': clean_n_number}
        
        try:
            logger.info(f"Looking up aircraft N{clean_n_number} in FAA registry...")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if aircraft was found
            if "The aircraft was not found" in response.text or "No records found" in response.text:
                logger.warning(f"Aircraft N{clean_n_number} not found in FAA registry")
                return None
            
            aircraft_data = {
                'n_number': f"N{clean_n_number}",
                'source': 'faa_registry',
                'lookup_date': datetime.now().isoformat(),
                'faa_url': f"{url}?{urlencode(params)}"
            }
            
            # Extract data from tables and divs
            self._extract_aircraft_details(soup, aircraft_data)
            self._extract_owner_details(soup, aircraft_data)
            
            return aircraft_data if len(aircraft_data) > 4 else None  # More than just metadata
            
        except requests.RequestException as e:
            logger.error(f"Error connecting to FAA registry: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing FAA data for N{clean_n_number}: {e}")
            return None
    
    def _extract_aircraft_details(self, soup: BeautifulSoup, data: Dict):
        """Extract aircraft specifications from HTML"""
        # Common patterns for aircraft data
        patterns = {
            'serial_number': [r'Serial Number[:\s]*([A-Z0-9-]+)', r'Serial[:\s]*([A-Z0-9-]+)'],
            'manufacturer': [r'Manufacturer[:\s]*([^<\n\r]+)', r'Make[:\s]*([^<\n\r]+)'],
            'model': [r'Model[:\s]*([^<\n\r]+)', r'Aircraft Model[:\s]*([^<\n\r]+)'],
            'year_manufactured': [r'Year Manufactured[:\s]*(\d{4})', r'Mfr Year[:\s]*(\d{4})'],
            'aircraft_type': [r'Aircraft Type[:\s]*([^<\n\r]+)', r'Type Aircraft[:\s]*([^<\n\r]+)'],
            'engine_type': [r'Engine Type[:\s]*([^<\n\r]+)', r'Type Engine[:\s]*([^<\n\r]+)'],
            'certificate_issue_date': [r'Certificate Issue Date[:\s]*([0-9/\-]+)', r'Issue Date[:\s]*([0-9/\-]+)'],
            'airworthiness_date': [r'Airworthiness Date[:\s]*([0-9/\-]+)', r'Date[:\s]*([0-9/\-]+)']
        }
        
        text = soup.get_text()
        
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    data[field] = match.group(1).strip()
                    break
    
    def _extract_owner_details(self, soup: BeautifulSoup, data: Dict):
        """Extract owner/registrant information from HTML"""
        patterns = {
            'owner_name': [
                r'Registrant[:\s]*([^<\n\r]+?)(?:\s*Address|\s*Street|\s*City|\s*$)',
                r'Name[:\s]*([^<\n\r]+?)(?:\s*Address|\s*Street|\s*City|\s*$)',
                r'Owner[:\s]*([^<\n\r]+?)(?:\s*Address|\s*Street|\s*City|\s*$)'
            ],
            'street_address': [
                r'Street[:\s]*([^<\n\r]+?)(?:\s*City|\s*State|\s*$)',
                r'Address[:\s]*([^<\n\r]+?)(?:\s*City|\s*State|\s*$)'
            ],
            'city': [r'City[:\s]*([^<\n\r,]+)', r'Municipality[:\s]*([^<\n\r,]+)'],
            'state': [r'State[:\s]*([A-Z]{2})', r'Province[:\s]*([A-Z]{2})'],
            'zip_code': [r'Zip[:\s]*([0-9\-]+)', r'Postal[:\s]*([0-9\-]+)'],
            'country': [r'Country[:\s]*([^<\n\r]+)', r'Nation[:\s]*([^<\n\r]+)']
        }
        
        text = soup.get_text()
        
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if value and value not in ['', 'N/A', 'None']:
                        data[field] = value
                        break


class OpenCorporatesReconcile:
    """Uses OpenCorporates Reconciliation API for company matching"""
    
    BASE_URL = "https://opencorporates.com/reconcile"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AircraftOwnershipResearch/2.0'
        })
    
    def search_companies(self, company_name: str, jurisdiction: str = "us", limit: int = 5) -> List[Dict]:
        """Search for companies using reconciliation API"""
        try:
            # Use the reconciliation API endpoint with jurisdiction
            url = f"{self.BASE_URL}/{jurisdiction}"
            
            params = {
                'query': company_name,
                'limit': limit
            }
            
            logger.info(f"Searching OpenCorporates for: {company_name}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('result', [])
            
            companies = []
            for result in results:
                company = self._parse_reconcile_result(result)
                if company:
                    companies.append(company)
            
            logger.info(f"Found {len(companies)} potential matches")
            return companies
            
        except requests.RequestException as e:
            logger.error(f"Error connecting to OpenCorporates: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing OpenCorporates response: {e}")
            return []
    
    def get_company_details(self, company_id: str) -> Optional[Dict]:
        """Get detailed company information using flyout endpoint"""
        try:
            url = f"{self.BASE_URL}/flyout"
            params = {'id': company_id}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            html_content = data.get('html', '')
            
            if html_content and "No company found" not in html_content:
                return self._parse_flyout_html(html_content, company_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting company details: {e}")
            return None
    
    def _parse_reconcile_result(self, result: Dict) -> Dict:
        """Parse reconciliation API result"""
        return {
            'id': result.get('id'),
            'name': result.get('name'),
            'score': result.get('score', 0),
            'match': result.get('match', False),
            'opencorporates_url': result.get('uri'),
            'source': 'opencorporates_reconcile'
        }
    
    def _parse_flyout_html(self, html_content: str, company_id: str) -> Dict:
        """Parse flyout HTML for detailed company info"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        details = {
            'id': company_id,
            'source': 'opencorporates_flyout'
        }
        
        # Extract title
        title_elem = soup.find('h1', {'id': 'oc-flyout-title'})
        if title_elem:
            details['name'] = title_elem.get_text().strip()
        
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


class AircraftOwnershipResearcher:
    """Main research coordinator"""
    
    def __init__(self):
        self.faa = FAAAircraftLookup()
        self.opencorp = OpenCorporatesReconcile()
    
    def research_aircraft(self, n_number: str) -> Dict:
        """Comprehensive aircraft ownership research"""
        logger.info(f"Starting research for aircraft {n_number}")
        
        result = {
            'n_number': n_number.upper(),
            'timestamp': datetime.now().isoformat(),
            'aircraft_data': None,
            'owner_analysis': None,
            'corporate_entities': [],
            'evidence_links': [],
            'confidence_score': 0,
            'recommendations': [],
            'errors': []
        }
        
        # Step 1: Get FAA aircraft data
        aircraft_data = self.faa.lookup_aircraft(n_number)
        if not aircraft_data:
            result['errors'].append(f"Aircraft {n_number} not found in FAA registry")
            return result
        
        result['aircraft_data'] = aircraft_data
        result['evidence_links'].append({
            'source': 'FAA Registry',
            'url': aircraft_data.get('faa_url', ''),
            'description': 'Official FAA aircraft registration lookup'
        })
        
        # Step 2: Analyze owner information
        owner_name = aircraft_data.get('owner_name', '')
        if not owner_name:
            result['errors'].append("No owner information found in FAA data")
            return result
        
        result['owner_analysis'] = self._analyze_owner_name(owner_name)
        
        # Step 3: Research corporate entities if business
        if result['owner_analysis']['is_likely_business']:
            logger.info(f"Researching business entity: {owner_name}")
            
            for search_term in result['owner_analysis']['search_terms']:
                companies = self.opencorp.search_companies(search_term, limit=3)
                
                for company in companies:
                    # Get detailed info
                    if company.get('id'):
                        details = self.opencorp.get_company_details(company['id'])
                        if details:
                            company.update(details)
                    
                    result['corporate_entities'].append(company)
                    
                    if company.get('opencorporates_url'):
                        result['evidence_links'].append({
                            'source': 'OpenCorporates',
                            'url': company['opencorporates_url'],
                            'description': f"Corporate record for {company.get('name', 'Unknown')}"
                        })
                
                # Don't overwhelm with too many searches
                if result['corporate_entities']:
                    break
        
        # Step 4: Calculate confidence and recommendations
        result['confidence_score'] = self._calculate_confidence_score(result)
        result['recommendations'] = self._generate_recommendations(result)
        
        return result
    
    def _analyze_owner_name(self, owner_name: str) -> Dict:
        """Analyze owner name to determine entity type"""
        business_indicators = [
            'LLC', 'INC', 'CORP', 'CORPORATION', 'COMPANY', 'CO', 'LTD', 'LIMITED',
            'TRUST', 'TRUSTEE', 'PARTNERSHIP', 'LP', 'LLP', 'HOLDINGS', 'GROUP',
            'AVIATION', 'AIRCRAFT', 'JETS', 'FLYING', 'CHARTER', 'MANAGEMENT',
            'ENTERPRISES', 'SERVICES', 'SOLUTIONS', 'VENTURES'
        ]
        
        name_upper = owner_name.upper()
        is_business = any(indicator in name_upper for indicator in business_indicators)
        
        # Generate search terms
        search_terms = []
        if is_business:
            # Clean name variations for better matching
            clean_name = owner_name
            for suffix in [' LLC', ' INC', ' CORP', ' LTD', ' CO']:
                clean_name = re.sub(f'{suffix}$', '', clean_name, flags=re.IGNORECASE)
            
            search_terms.append(clean_name.strip())
            search_terms.append(owner_name)  # Also try full name
        
        return {
            'original_name': owner_name,
            'is_likely_business': is_business,
            'search_terms': list(set(search_terms)),  # Remove duplicates
            'entity_type': self._classify_entity_type(owner_name)
        }
    
    def _classify_entity_type(self, name: str) -> str:
        """Classify entity type from name"""
        name_upper = name.upper()
        
        if 'TRUST' in name_upper:
            return 'Trust'
        elif any(x in name_upper for x in ['LLC', 'LIMITED LIABILITY']):
            return 'Limited Liability Company'
        elif any(x in name_upper for x in ['INC', 'CORP', 'CORPORATION']):
            return 'Corporation'
        elif any(x in name_upper for x in ['LP', 'LLP', 'PARTNERSHIP']):
            return 'Partnership'
        elif any(x in name_upper for x in ['HOLDINGS', 'GROUP', 'MANAGEMENT']):
            return 'Holding/Management Company'
        else:
            return 'Individual/Unknown'
    
    def _calculate_confidence_score(self, result: Dict) -> int:
        """Calculate confidence score based on data quality"""
        score = 0
        
        # Basic aircraft data found
        if result['aircraft_data']:
            score += 30
        
        # Owner name quality
        if result['owner_analysis']:
            if result['owner_analysis']['is_likely_business']:
                score += 20
            if len(result['owner_analysis']['original_name']) > 5:
                score += 10
        
        # Corporate entity matches
        if result['corporate_entities']:
            score += 20
            
            # Bonus for high-scoring matches
            high_score_matches = [c for c in result['corporate_entities'] if c.get('score', 0) > 70]
            if high_score_matches:
                score += 15
            
            # Penalty for too many low-quality matches
            if len(result['corporate_entities']) > 5:
                score -= 10
        
        # Evidence links
        if len(result['evidence_links']) >= 2:
            score += 5
        
        return max(0, min(score, 100))
    
    def _generate_recommendations(self, result: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if result['confidence_score'] < 40:
            recommendations.append("Low confidence score - manual verification strongly recommended")
        
        if not result['corporate_entities'] and result['owner_analysis']['is_likely_business']:
            recommendations.append("Business entity detected but no corporate records found - check state registries manually")
        
        if result['corporate_entities']:
            high_scores = [c for c in result['corporate_entities'] if c.get('score', 0) > 80]
            if not high_scores:
                recommendations.append("No high-confidence corporate matches - review results carefully")
        
        if result['owner_analysis']['entity_type'] == 'Trust':
            recommendations.append("Trust ownership - beneficial owners may not be publicly available")
        
        if len(result['corporate_entities']) > 3:
            recommendations.append("Multiple corporate matches found - verify correct entity using address/state")
        
        return recommendations
    
    def batch_research(self, n_numbers: List[str]) -> List[Dict]:
        """Research multiple aircraft"""
        results = []
        
        for i, n_number in enumerate(n_numbers):
            logger.info(f"Processing {i+1}/{len(n_numbers)}: {n_number}")
            
            result = self.research_aircraft(n_number)
            results.append(result)
            
            # Rate limiting to be respectful
            time.sleep(2)
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Aircraft Ownership Research Tool v2')
    parser.add_argument('n_number', nargs='?', help='Aircraft N-number to research')
    parser.add_argument('--batch', help='File containing list of N-numbers')
    parser.add_argument('--output', help='Output JSON file for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    researcher = AircraftOwnershipResearcher()
    
    if args.batch:
        # Batch processing
        try:
            with open(args.batch, 'r') as f:
                n_numbers = [line.strip() for line in f if line.strip()]
            
            results = researcher.batch_research(n_numbers)
            
            # Save results
            output_file = args.output or f"aircraft_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Print summary
            print(f"\n{'='*60}")
            print(f"BATCH RESEARCH COMPLETE - {len(results)} aircraft processed")
            print(f"Results saved to: {output_file}")
            print(f"{'='*60}")
            
            for result in results:
                score = result.get('confidence_score', 0)
                entities = len(result.get('corporate_entities', []))
                errors = len(result.get('errors', []))
                status = "✓" if score > 50 and not errors else "⚠" if not errors else "✗"
                print(f"  {status} {result['n_number']}: {score}% confidence, {entities} entities")
        
        except FileNotFoundError:
            print(f"Error: Batch file '{args.batch}' not found")
            return
    
    elif args.n_number:
        # Single aircraft research
        result = researcher.research_aircraft(args.n_number)
        
        # Display results
        print(f"\n{'='*70}")
        print(f"AIRCRAFT OWNERSHIP RESEARCH: {result['n_number']}")
        print(f"{'='*70}")
        
        if result.get('errors'):
            print(f"\n❌ ERRORS:")
            for error in result['errors']:
                print(f"   {error}")
            return
        
        # Aircraft Information
        aircraft = result['aircraft_data']
        print(f"\n✈️  AIRCRAFT INFORMATION:")
        print(f"   Model: {aircraft.get('manufacturer', 'N/A')} {aircraft.get('model', 'N/A')}")
        print(f"   Serial: {aircraft.get('serial_number', 'N/A')}")
        print(f"   Year: {aircraft.get('year_manufactured', 'N/A')}")
        print(f"   Type: {aircraft.get('aircraft_type', 'N/A')}")
        
        # Owner Information
        print(f"\n👤 OWNER INFORMATION:")
        print(f"   Name: {aircraft.get('owner_name', 'N/A')}")
        if aircraft.get('street_address'):
            print(f"   Address: {aircraft.get('street_address')}")
        if aircraft.get('city') or aircraft.get('state'):
            city_state = f"{aircraft.get('city', '')}, {aircraft.get('state', '')} {aircraft.get('zip_code', '')}".strip(', ')
            print(f"   Location: {city_state}")
        print(f"   Entity Type: {result['owner_analysis']['entity_type']}")
        
        # Corporate Entities
        if result['corporate_entities']:
            print(f"\n🏢 CORPORATE ENTITIES ({len(result['corporate_entities'])} found):")
            for i, entity in enumerate(result['corporate_entities'], 1):
                score = entity.get('score', 0)
                confidence = "🔥" if score > 80 else "✓" if score > 60 else "⚠"
                print(f"   {i}. {confidence} {entity.get('name', 'Unknown')} (Score: {score})")
                if entity.get('status'):
                    print(f"      Status: {entity['status']}")
                if entity.get('company_type'):
                    print(f"      Type: {entity['company_type']}")
                if entity.get('jurisdiction'):
                    print(f"      Jurisdiction: {entity['jurisdiction']}")
                if entity.get('address'):
                    print(f"      Address: {entity['address']}")
        
        # Evidence Links
        if result['evidence_links']:
            print(f"\n🔗 EVIDENCE LINKS:")
            for link in result['evidence_links']:
                print(f"   • {link['source']}: {link['url']}")
        
        # Assessment
        score = result['confidence_score']
        confidence_emoji = "🔥" if score > 80 else "✅" if score > 60 else "⚠️" if score > 40 else "❌"
        print(f"\n📊 CONFIDENCE ASSESSMENT: {confidence_emoji} {score}%")
        
        if result['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in result['recommendations']:
                print(f"   • {rec}")
        
        # Save single result if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {args.output}")
    
    else:
        print("Aircraft Ownership Research Tool v2")
        print("\nUsage:")
        print("  python aircraft_lookup.py N12345              # Single aircraft lookup")
        print("  python aircraft_lookup.py --batch list.txt    # Batch processing")
        print("  python aircraft_lookup.py N12345 --output result.json")
        print("\nExample N-numbers to try:")
        print("  N1KE, N7777G, N123AB, N456CD")


if __name__ == "__main__":
    main()