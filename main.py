
# main.py
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from utils.logging_config import setup_logging
from agent.graph import AircraftResearchAgent
import logging

def setup_environment():
    """Setup environment variables and logging."""
    
    # Setup logging
    logger = setup_logging("INFO", "aircraft_research.log")
    
    # Setup LangSmith tracing
    if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        logger.info("LangSmith tracing enabled")
    
    return logger

def demo_aircraft_research():
    """Demo function to show aircraft research capabilities."""
    
    logger = setup_environment()
    
    try:
        # Initialize agent
        logger.info("Initializing Aircraft Research Agent...")
        agent = AircraftResearchAgent()
        
        # Demo with sample N-numbers
        test_n_numbers = ["N540JT", "N421AB", "N123XY"]  # Replace with real examples
        
        print("\n🛩️  Aircraft Ownership Research Agent Demo")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Research specific N-number")
            print("2. Run demo with sample N-numbers")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                n_number = input("Enter aircraft N-number (e.g., N540JT): ").strip()
                if n_number:
                    print(f"\n🔍 Researching {n_number}...")
                    result = agent.research_aircraft(n_number)
                    print_research_results(result)
                
            elif choice == "2":
                for n_number in test_n_numbers:
                    print(f"\n🔍 Researching {n_number}...")
                    result = agent.research_aircraft(n_number, thread_id=f"demo_{n_number}")
                    print_research_results(result)
                    
                    input("\nPress Enter to continue to next aircraft...")
                
            elif choice == "3":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")
                
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        print(f"Error: {str(e)}")

def print_research_results(result: dict):
    """Print formatted research results."""
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print("\n📋 Research Results:")
    print("-" * 30)
    
    # Extract information from the final message
    if "messages" in result and result["messages"]:
        final_message = result["messages"][-1]
        if hasattr(final_message, 'content'):
            print(final_message.content)
        else:
            print("Research completed. Check logs for detailed results.")
    
    # Print any additional structured data
    for key in ["faa_data", "flightaware_data", "search_results", "final_result"]:
        if key in result and result[key]:
            print(f"\n{key.replace('_', ' ').title()}:")
            print(f"  Available: ✅")

if __name__ == "__main__":
    demo_aircraft_research()
