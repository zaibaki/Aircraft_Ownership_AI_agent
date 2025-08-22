# app/services/aircraft_service.py
import asyncio
import logging
from typing import Dict, Any
from agent.graph import AircraftResearchAgent

logger = logging.getLogger("aircraft_research_api.service")

class AircraftResearchService:
    """Service for aircraft research operations."""
    
    def __init__(self):
        self.agent = AircraftResearchAgent()
        logger.info("Aircraft Research Service initialized")
    
    async def research_aircraft(self, n_number: str) -> Dict[str, Any]:
        """Research aircraft ownership information asynchronously."""
        try:
            logger.info(f"Starting aircraft research for: {n_number}")
            
            # Run the agent in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.agent.research_aircraft, 
                n_number
            )
            
            logger.info(f"Completed aircraft research for: {n_number}")
            return result
            
        except Exception as e:
            logger.error(f"Error in aircraft research service: {str(e)}")
            return {"error": str(e), "n_number": n_number}
