#!/usr/bin/env python3
"""
Fixed LangGraph implementation with proper tool calling
"""

from typing import Dict, Literal
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
import logging

from agents.state import AircraftResearchState
from tools.faa_tools import faa_database_lookup, faa_web_scraper
from tools.corporate_tools import opencorporates_search
from config.settings import OPENAI_API_KEY
from config.prompts import SYSTEM_PROMPT
from config.langsmith_config import traceable
from utils.logging_config import tracker, track_tool_execution

logger = logging.getLogger(__name__)

# Initialize LLM
llm = init_chat_model("openai:gpt-4", api_key=OPENAI_API_KEY)

# Define available tools
tools = [
    faa_database_lookup,
    faa_web_scraper,
    opencorporates_search,
]

# Create LLM with tools
llm_with_tools = llm.bind_tools(tools)

@traceable
@track_tool_execution("agent_node")
def agent_node(state: AircraftResearchState) -> AircraftResearchState:
    """
    Main agent node that processes messages and makes tool calls
    """
    messages = state.get("messages", [])
    
    # Add system prompt if this is the first interaction
    if not messages:
        system_message = HumanMessage(content=SYSTEM_PROMPT)
        messages = [system_message]
    
    # Add the user query as a message if not already present
    query = state.get("query", "")
    if query and not any("research" in str(msg.content).lower() for msg in messages):
        user_message = HumanMessage(content=f"Research aircraft ownership for: {query}")
        messages.append(user_message)
    
    logger.info(f"Agent processing {len(messages)} messages")
    
    try:
        # Get LLM response with tools
        response = llm_with_tools.invoke(messages)
        
        # Log token usage if available
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            logger.info(f"Token usage - Input: {usage.get('input_tokens', 0)}, Output: {usage.get('output_tokens', 0)}")
            tracker.total_tokens += usage.get('total_tokens', 0)
        
        # Update messages
        updated_messages = messages + [response]
        state["messages"] = updated_messages
        
        # Log tool calls if any
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_names = [tc["name"] for tc in response.tool_calls]
            logger.info(f"Agent requesting tools: {tool_names}")
        
        return state
        
    except Exception as e:
        logger.error(f"Agent node failed: {e}")
        error_message = AIMessage(content=f"Agent error: {str(e)}")
        state["messages"] = messages + [error_message]
        return state

@traceable
def should_continue(state: AircraftResearchState) -> Literal["tools", "end"]:
    """
    Determine if we should continue to tools or end
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    # Check if we have tool calls to execute
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"Continuing to tools: {[tc['name'] for tc in last_message.tool_calls]}")
        return "tools"
    
    logger.info("No tool calls found, ending conversation")
    return "end"

@traceable
@track_tool_execution("analysis_node")
def analysis_node(state: AircraftResearchState) -> AircraftResearchState:
    """
    Analyze the research results and provide summary
    """
    messages = state.get("messages", [])
    
    # Extract information from tool responses
    aircraft_info = {}
    corporate_entities = []
    evidence_links = []
    
    for msg in messages:
        if isinstance(msg, ToolMessage):
            try:
                # Parse tool results
                if msg.name == "faa_database_lookup" or msg.name == "faa_web_scraper":
                    content = eval(msg.content) if isinstance(msg.content, str) else msg.content
                    if isinstance(content, dict) and not content.get("error"):
                        aircraft_info.update(content)
                        
                elif msg.name == "opencorporates_search":
                    content = eval(msg.content) if isinstance(msg.content, str) else msg.content
                    if isinstance(content, list):
                        corporate_entities.extend(content)
                        
            except Exception as e:
                logger.warning(f"Failed to parse tool message: {e}")
    
    # Generate evidence links
    if aircraft_info.get("registry_url"):
        evidence_links.append({
            "source": "FAA Registry",
            "url": aircraft_info["registry_url"],
            "description": "Official aircraft registration"
        })
    
    for entity in corporate_entities:
        if entity.get("opencorporates_url"):
            evidence_links.append({
                "source": "OpenCorporates",
                "url": entity["opencorporates_url"],
                "description": f"Corporate record for {entity.get('name', 'Unknown')}"
            })
    
    # Calculate confidence score
    confidence_score = 0
    justification_parts = []
    
    if aircraft_info and not aircraft_info.get("error"):
        confidence_score += 30
        justification_parts.append("Aircraft found in records (+30)")
        
        if aircraft_info.get("owner_name"):
            confidence_score += 20
            justification_parts.append("Owner information available (+20)")
    
    if corporate_entities:
        high_score_entities = [e for e in corporate_entities if e.get("score", 0) > 70]
        if high_score_entities:
            confidence_score += 25
            justification_parts.append("High-confidence corporate matches (+25)")
        else:
            confidence_score += 15
            justification_parts.append("Corporate entities found (+15)")
    
    confidence_score = min(confidence_score, 100)
    justification = "; ".join(justification_parts) if justification_parts else "Limited data available"
    
    # Update state with analysis results
    state["aircraft_info"] = aircraft_info
    state["corporate_entities"] = corporate_entities
    state["evidence_links"] = evidence_links
    state["confidence_score"] = confidence_score
    state["confidence_justification"] = justification
    state["research_status"] = "complete"
    
    # Add summary message
    summary_message = AIMessage(content=f"Research completed with {confidence_score}% confidence. Found aircraft data: {bool(aircraft_info)}, Corporate entities: {len(corporate_entities)}")
    state["messages"].append(summary_message)
    
    logger.info(f"Analysis complete - Confidence: {confidence_score}%, Entities: {len(corporate_entities)}")
    return state

def create_aircraft_research_graph():
    """
    Create and configure the aircraft research graph with proper tool calling
    """
    logger.info("Creating aircraft research graph...")
    
    # Create graph
    graph_builder = StateGraph(AircraftResearchState)
    
    # Add nodes
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_node("analysis", analysis_node)
    
    # Add edges
    graph_builder.add_edge(START, "agent")
    
    # Add conditional edges
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": "analysis"
        }
    )
    
    # After tools, go back to agent for processing
    graph_builder.add_edge("tools", "agent")
    
    # Analysis is the final step
    graph_builder.add_edge("analysis", END)
    
    # Add memory
    memory = InMemorySaver()
    
    # Compile graph
    graph = graph_builder.compile(checkpointer=memory)
    
    logger.info("Aircraft research graph created successfully")
    return graph