#!/usr/bin/env python3
"""
Aircraft Ownership Research Agent - Fixed Version
Addresses tool calling errors and large payload issues
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import traceback

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Set environment variables manually.")

# Check for required environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not set. Please add it to your .env file.")
    sys.exit(1)

# Setup logging before other imports
from utils.logging_config import setup_logging, tracker
setup_logging()

import logging
logger = logging.getLogger(__name__)

# Setup optimized LangSmith
from config.langsmith_config import setup_langsmith_optimized
setup_langsmith_optimized()

# Import the fixed graph
from agents.graph_fixed import create_aircraft_research_graph
from agents.state import AircraftResearchState

def format_research_output(result: AircraftResearchState) -> str:
    """Format research results for display"""
    
    output = []
    output.append("=" * 80)
    output.append("AIRCRAFT OWNERSHIP INTELLIGENCE REPORT")
    output.append("=" * 80)
    
    # Aircraft Information
    aircraft_info = result.get("aircraft_info", {})
    if aircraft_info and not aircraft_info.get("error"):
        output.append("\n✈️ AIRCRAFT INFORMATION:")
        output.append(f"   Tail Number: {aircraft_info.get('n_number', 'N/A')}")
        
        # Try different field names for manufacturer
        manufacturer = aircraft_info.get('manufacturer') or aircraft_info.get('manufacturer_name', 'N/A')
        output.append(f"   Manufacturer: {manufacturer}")
        
        output.append(f"   Model: {aircraft_info.get('model', 'N/A')}")
        output.append(f"   Year: {aircraft_info.get('year_manufactured', 'N/A')}")
        output.append(f"   Serial: {aircraft_info.get('serial_number', 'N/A')}")
        output.append(f"   Type: {aircraft_info.get('aircraft_type', 'N/A')}")
        output.append(f"   Status: {aircraft_info.get('status', 'N/A')}")
    elif aircraft_info and aircraft_info.get("error"):
        output.append(f"\n❌ AIRCRAFT LOOKUP ERROR: {aircraft_info['error']}")
    
    # Ownership Information
    if aircraft_info and aircraft_info.get("owner_name"):
        output.append("\n👤 OWNERSHIP STRUCTURE:")
        output.append(f"   Registered Owner: {aircraft_info.get('owner_name', 'N/A')}")
        
        # Try to classify entity type
        owner_name = aircraft_info.get('owner_name', '').upper()
        if 'TRUST' in owner_name:
            entity_type = "Trust"
        elif any(x in owner_name for x in ['LLC', 'LIMITED LIABILITY']):
            entity_type = "Limited Liability Company"
        elif any(x in owner_name for x in ['INC', 'CORP', 'CORPORATION']):
            entity_type = "Corporation"
        else:
            entity_type = "Individual/Unknown"
        
        output.append(f"   Entity Type: {entity_type}")
        
        if aircraft_info.get("street"):
            output.append(f"   Address: {aircraft_info.get('street', '')}")
            city_state = f"{aircraft_info.get('city', '')}, {aircraft_info.get('state', '')} {aircraft_info.get('zip_code', '')}".strip(', ')
            if city_state:
                output.append(f"   Location: {city_state}")
    
    # Corporate Entities
    corporate_entities = result.get("corporate_entities", [])
    if corporate_entities:
        output.append(f"\n🏢 CORPORATE ENTITIES ({len(corporate_entities)} found):")
        for i, entity in enumerate(corporate_entities[:3], 1):  # Show top 3
            score = entity.get("score", 0)
            confidence_indicator = "🔥" if score > 80 else "✅" if score > 60 else "⚠️"
            output.append(f"   {i}. {confidence_indicator} {entity.get('name', 'Unknown')} (Score: {score}%)")
            if entity.get("status"):
                output.append(f"      Status: {entity['status']}")
            if entity.get("jurisdiction"):
                output.append(f"      Jurisdiction: {entity['jurisdiction']}")
    
    # Evidence Links
    evidence_links = result.get("evidence_links", [])
    if evidence_links:
        output.append("\n🔗 EVIDENCE LINKS:")
        for link in evidence_links:
            output.append(f"   • {link.get('source', 'Unknown')}: {link.get('url', 'N/A')}")
    
    # Add FAA registry link if we have aircraft info
    if aircraft_info and aircraft_info.get("n_number"):
        n_num = aircraft_info["n_number"].replace("N", "")
        faa_url = f"https://registry.faa.gov/AircraftInquiry/Search/NNumberResult?nNumberTxt={n_num}"
        if not any("FAA Registry" in link.get("source", "") for link in evidence_links):
            output.append(f"   • FAA Registry: {faa_url}")
    
    # Confidence Assessment
    confidence_score = result.get("confidence_score", 0)
    confidence_emoji = "🔥" if confidence_score > 80 else "✅" if confidence_score > 60 else "⚠️" if confidence_score > 40 else "❌"
    output.append(f"\n📊 CONFIDENCE ASSESSMENT: {confidence_emoji} {confidence_score}%")
    
    justification = result.get("confidence_justification", "")
    if justification:
        output.append(f"   Justification: {justification}")
    
    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        output.append("\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            output.append(f"   • {rec}")
    
    # Research Status
    research_status = result.get("research_status", "unknown")
    output.append(f"\n📈 Research Status: {research_status.upper()}")
    
    return "\n".join(output)

def save_results(result: AircraftResearchState, filename: str = None):
    """Save research results to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query = result.get("query", "unknown").replace(" ", "_")
        filename = f"aircraft_research_{query}_{timestamp}.json"
    
    # Convert result to serializable format
    serializable_result = {}
    for key, value in result.items():
        if key == "messages":
            # Convert messages to dict format
            serializable_result[key] = [
                {"type": type(msg).__name__, "content": str(msg.content)} 
                for msg in value
            ]
        else:
            serializable_result[key] = value
    
    with open(filename, 'w') as f:
        json.dump(serializable_result, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(description='Aircraft Ownership Intelligence Agent - Fixed Version')
    parser.add_argument('query', nargs='?', help='Aircraft N-number to research')
    parser.add_argument('--save', help='Save results to specified file')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--thread-id', default='default', help='Thread ID for conversation memory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Aircraft Ownership Intelligence Agent")
    
    # Create graph
    try:
        graph = create_aircraft_research_graph()
        logger.info("Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        traceback.print_exc()
        return
    
    if args.interactive or not args.query:
        # Interactive mode
        print("Aircraft Ownership Intelligence Agent")
        print("Enter aircraft N-numbers (e.g., N123AB) or 'quit' to exit")
        
        while True:
            try:
                query = input("\nEnter aircraft identifier: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                # Run research
                config = {"configurable": {"thread_id": args.thread_id}}
                
                initial_state = {
                    "query": query,
                    "messages": [],
                    "research_status": "started",
                    "confidence_score": 0,
                    "evidence_links": [],
                    "corporate_entities": [],
                    "recommendations": []
                }
                
                print(f"\n🔍 Researching {query}...")
                logger.info(f"Starting research for {query}")
                
                # Stream the graph execution to show progress
                final_state = None
                for event in graph.stream(initial_state, config, stream_mode="values"):
                    # Track progress
                    status = event.get("research_status", "")
                    if status:
                        print(f"Status: {status}")
                    
                    final_state = event
                
                if not final_state:
                    # Fallback: invoke directly if streaming fails
                    logger.warning("Streaming failed, falling back to direct invocation")
                    final_state = graph.invoke(initial_state, config)
                
                # Display results
                print(format_research_output(final_state))
                
                # Show execution summary
                tracker.print_summary()
                
                # Save if requested
                if args.save:
                    save_results(final_state, args.save)
                
            except KeyboardInterrupt:
                print("\nOperation cancelled")
                break
            except Exception as e:
                logger.error(f"Research failed for {query}: {e}")
                print(f"Error: {e}")
                if args.verbose:
                    traceback.print_exc()
    
    else:
        # Single query mode
        config = {"configurable": {"thread_id": args.thread_id}}
        
        initial_state = {
            "query": args.query,
            "messages": [],
            "research_status": "started",
            "confidence_score": 0,
            "evidence_links": [],
            "corporate_entities": [],
            "recommendations": []
        }
        
        print(f"🔍 Researching {args.query}...")
        logger.info(f"Starting research for {args.query}")
        
        # Run research
        try:
            final_state = graph.invoke(initial_state, config)
            
            # Display results
            print(format_research_output(final_state))
            
            # Show execution summary
            tracker.print_summary()
            
            # Save if requested
            if args.save:
                save_results(final_state, args.save)
        
        except Exception as e:
            logger.error(f"Research failed: {e}")
            print(f"Research failed: {e}")
            if args.verbose:
                traceback.print_exc()

if __name__ == "__main__":
    main()