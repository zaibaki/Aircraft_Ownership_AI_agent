
# agent/graph.py
from typing import Annotated, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
import logging

from tools.faa_scraper import FAARegistrationScraper
from tools.flightaware_scraper import FlightAwareScraper
from tools.tavily_search import TavilyOwnershipSearch
from tools.ownership_analyzer import OwnershipAnalyzer
from models.schemas import AircraftResearchResult
from agent.prompts import SYSTEM_PROMPT

logger = logging.getLogger("aircraft_research.agent")

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    n_number: str
    faa_data: Dict[str, Any]
    flightaware_data: Dict[str, Any]
    search_results: list
    final_result: Dict[str, Any]

class AircraftResearchAgent:
    """Main LangGraph agent for aircraft ownership research."""
    
    def __init__(self, model_name: str = "openai:gpt-4o-mini"):
        self.logger = logging.getLogger("aircraft_research.agent.AircraftResearchAgent")
        
        # Initialize tools
        self.tools = [
            FAARegistrationScraper(),
            FlightAwareScraper(), 
            TavilyOwnershipSearch(),
            OwnershipAnalyzer()
        ]
        
        # Initialize LLM with tools using LangChain's init_chat_model
        self.llm = init_chat_model(model_name, temperature=0)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build graph
        self.graph = self._build_graph()
        
        self.logger.info("Aircraft Research Agent initialized successfully")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create state graph
        graph_builder = StateGraph(AgentState)
        
        # Add chatbot node
        def chatbot(state: AgentState):
            self.logger.info(f"Chatbot processing state with {len(state.get('messages', []))} messages")
            
            # Add system prompt if this is the first message
            messages = state["messages"]
            if len(messages) == 1:  # Only user message
                system_message = {"role": "system", "content": SYSTEM_PROMPT}
                messages = [system_message] + messages
            
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        graph_builder.add_node("chatbot", chatbot)
        
        # Add tool node
        tool_node = ToolNode(tools=self.tools)
        graph_builder.add_node("tools", tool_node)
        
        # Add edges
        graph_builder.add_conditional_edges("chatbot", tools_condition)
        graph_builder.add_edge("tools", "chatbot")
        graph_builder.add_edge(START, "chatbot")
        
        # Compile with memory
        memory = InMemorySaver()
        return graph_builder.compile(checkpointer=memory)
    
    def research_aircraft(self, n_number: str, thread_id: str = "default") -> Dict[str, Any]:
        """Research aircraft ownership information."""
        try:
            self.logger.info(f"Starting aircraft research for N-number: {n_number}")
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Initial user message
            user_message = {
                "role": "user", 
                "content": f"Please research the ownership information for aircraft N-number: {n_number}. "
                          f"Use all available tools to gather comprehensive ownership data including "
                          f"decision maker identification and contact information."
            }
            
            # Stream the graph execution
            final_state = None
            for event in self.graph.stream(
                {"messages": [user_message], "n_number": n_number},
                config,
                stream_mode="values"
            ):
                final_state = event
                if "messages" in event and event["messages"]:
                    last_message = event["messages"][-1]
                    self.logger.debug(f"Agent step: {last_message.content[:100]}...")
            
            self.logger.info(f"Aircraft research completed for {n_number}")
            return final_state
            
        except Exception as e:
            self.logger.error(f"Error in aircraft research for {n_number}: {str(e)}")
            return {"error": str(e), "n_number": n_number}
