# tools/base.py
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import Field, ConfigDict

class BaseResearchTool(BaseTool, ABC):
    """Base class for all aircraft research tools."""
    
    # Configure Pydantic to allow arbitrary types and extra fields
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra='allow'
    )
    
    # Properly annotate these fields to satisfy Pydantic
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set logger as an object attribute, not a model field
        object.__setattr__(self, 'logger', logging.getLogger(f"aircraft_research.tools.{self.__class__.__name__}"))
    
    def _log_tool_start(self, inputs: Dict[str, Any]) -> None:
        """Log tool execution start."""
        self.logger.info(f"Starting {self.name} with inputs: {inputs}")
    
    def _log_tool_end(self, result: Any) -> None:
        """Log tool execution end."""
        self.logger.info(f"Completed {self.name}")
        self.logger.debug(f"Result preview: {str(result)[:200]}...")
    
    def _log_error(self, error: Exception, inputs: Dict[str, Any]) -> None:
        """Log tool errors."""
        self.logger.error(f"Error in {self.name} with inputs {inputs}: {str(error)}")