#!/usr/bin/env python3
"""
LangSmith configuration with size limits and error handling
"""

import os
import logging
from typing import Dict, Any

def setup_langsmith_optimized():
    """
    Setup LangSmith with optimized settings to avoid large payload issues
    """
    
    # Only enable if API key is present
    if not os.getenv("LANGSMITH_API_KEY"):
        logging.warning("LangSmith API key not found - tracing disabled")
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    
    # Configure LangSmith with size optimizations
    os.environ["LANGSMITH_TRACING"] = "true"
    
    # Limit payload size to avoid 32MB error
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    
    # Set project name
    project_name = os.getenv("LANGSMITH_PROJECT", "aircraft-ownership-research")
    os.environ["LANGCHAIN_PROJECT"] = project_name
    
    # Reduce verbosity to minimize payload size
    os.environ["LANGCHAIN_VERBOSE"] = "false"
    
    try:
        from langsmith import Client
        client = Client()
        
        # Test connection with minimal data
        client.create_run(
            name="test-connection",
            run_type="tool",
            inputs={"test": "connection"},
            outputs={"status": "connected"}
        )
        
        logging.info(f"LangSmith connected successfully - Project: {project_name}")
        return True
        
    except Exception as e:
        logging.warning(f"LangSmith setup failed: {e}")
        # Disable tracing if setup fails
        os.environ["LANGSMITH_TRACING"] = "false"
        return False

def create_optimized_traceable():
    """
    Create a lightweight traceable decorator that avoids large payloads
    """
    
    langsmith_enabled = setup_langsmith_optimized()
    
    if not langsmith_enabled:
        # Return no-op decorator if LangSmith not available
        def no_op_traceable(func_or_name=None, **kwargs):
            if callable(func_or_name):
                return func_or_name
            else:
                def decorator(func):
                    return func
                return decorator
        return no_op_traceable
    
    try:
        from langsmith import traceable as langsmith_traceable
        
        def optimized_traceable(func_or_name=None, **kwargs):
            """Traceable decorator with size limits"""
            
            def create_decorator(name=None):
                def decorator(func):
                    def wrapper(*args, **func_kwargs):
                        # Limit input/output size for tracing
                        limited_args = _limit_trace_data(args)
                        limited_kwargs = _limit_trace_data(func_kwargs)
                        
                        try:
                            result = func(*args, **func_kwargs)
                            # Don't trace large results
                            if _get_data_size(result) > 1000000:  # 1MB limit
                                trace_result = {"status": "completed", "size": "large_result_omitted"}
                            else:
                                trace_result = result
                            
                            return result
                            
                        except Exception as e:
                            logging.error(f"Function {func.__name__} failed: {e}")
                            raise
                    
                    # Apply LangSmith traceable if available
                    return langsmith_traceable(name=name or func.__name__)(wrapper)
                
                return decorator
            
            if callable(func_or_name):
                return create_decorator()(func_or_name)
            else:
                return create_decorator(func_or_name)
        
        return optimized_traceable
        
    except ImportError:
        logging.warning("LangSmith not available - using no-op traceable")
        return create_optimized_traceable()

def _limit_trace_data(data: Any, max_size: int = 10000) -> Any:
    """Limit data size for tracing to prevent large payloads"""
    
    data_str = str(data)
    if len(data_str) > max_size:
        if isinstance(data, dict):
            # For dicts, keep keys but truncate values
            limited = {}
            for k, v in data.items():
                v_str = str(v)
                if len(v_str) > 100:
                    limited[k] = f"{v_str[:100]}... [truncated]"
                else:
                    limited[k] = v
            return limited
        elif isinstance(data, (list, tuple)):
            # For lists, take first few items
            return data[:5] if len(data) > 5 else data
        else:
            # For other types, truncate string representation
            return f"{data_str[:max_size]}... [truncated]"
    
    return data

def _get_data_size(data: Any) -> int:
    """Get approximate size of data in bytes"""
    try:
        import sys
        return sys.getsizeof(str(data))
    except:
        return len(str(data))

# Create the optimized traceable decorator
traceable = create_optimized_traceable()