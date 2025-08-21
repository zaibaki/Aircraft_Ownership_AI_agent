# tests/test_agent.py
import pytest
from unittest.mock import Mock, patch
from agent.graph import AircraftResearchAgent

class TestAircraftResearchAgent:
    
    def test_agent_initialization(self):
        agent = AircraftResearchAgent()
        assert agent.graph is not None
        assert len(agent.tools) == 4
    
    @patch('agent.graph.init_chat_model')
    def test_research_aircraft_basic(self, mock_llm):
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        agent = AircraftResearchAgent()
        
        # This would require more extensive mocking for a real test
        # Just testing that the method exists and accepts parameters
        assert hasattr(agent, 'research_aircraft')
