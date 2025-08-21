#!/usr/bin/env python3
"""
Logging configuration and tool execution tracking
"""

import logging
import time
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime

class ToolExecutionTracker:
    """Track tool execution, timing, and token usage"""
    
    def __init__(self):
        self.executions = []
        self.total_tokens = 0
        self.total_cost = 0.0
        
        # Token costs per model (approximation)
        self.token_costs = {
            'gpt-4': {'input': 0.03/1000, 'output': 0.06/1000},
            'gpt-4-turbo': {'input': 0.01/1000, 'output': 0.03/1000},
            'gpt-3.5-turbo': {'input': 0.0015/1000, 'output': 0.002/1000}
        }
    
    def log_tool_execution(self, tool_name: str, inputs: Dict, outputs: Any, 
                          execution_time: float, tokens_used: Optional[Dict] = None):
        """Log a tool execution"""
        execution = {
            'timestamp': datetime.now().isoformat(),
            'tool_name': tool_name,
            'inputs': str(inputs)[:200] + '...' if len(str(inputs)) > 200 else str(inputs),
            'output_type': type(outputs).__name__,
            'output_size': len(str(outputs)),
            'execution_time': execution_time,
            'tokens_used': tokens_used or {},
            'success': not isinstance(outputs, dict) or not outputs.get('error')
        }
        
        self.executions.append(execution)
        
        if tokens_used:
            self.total_tokens += tokens_used.get('total_tokens', 0)
            
        logging.info(
            f"Tool executed: {tool_name} | "
            f"Time: {execution_time:.2f}s | "
            f"Success: {execution['success']} | "
            f"Tokens: {tokens_used.get('total_tokens', 0) if tokens_used else 0}"
        )
    
    def get_summary(self) -> Dict:
        """Get execution summary"""
        successful = sum(1 for ex in self.executions if ex['success'])
        failed = len(self.executions) - successful
        total_time = sum(ex['execution_time'] for ex in self.executions)
        
        return {
            'total_executions': len(self.executions),
            'successful': successful,
            'failed': failed,
            'total_time': total_time,
            'total_tokens': self.total_tokens,
            'estimated_cost': self.total_cost
        }
    
    def print_summary(self):
        """Print execution summary"""
        summary = self.get_summary()
        print(f"\n--- TOOL EXECUTION SUMMARY ---")
        print(f"Total executions: {summary['total_executions']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Total time: {summary['total_time']:.2f}s")
        print(f"Total tokens: {summary['total_tokens']}")
        print(f"Estimated cost: ${summary['estimated_cost']:.4f}")

# Global tracker instance
tracker = ToolExecutionTracker()

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('aircraft_research.log')
        ]
    )
    
    # Reduce LangSmith logging verbosity
    logging.getLogger('langsmith').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

def track_tool_execution(tool_name: str):
    """Decorator to track tool execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log tool start
            inputs = {'args': args, 'kwargs': kwargs}
            logging.info(f"Starting tool: {tool_name}")
            logging.debug(f"Tool inputs: {inputs}")
            
            try:
                # Execute tool
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Extract token usage if available
                tokens_used = None
                if hasattr(result, 'usage_metadata'):
                    tokens_used = {
                        'input_tokens': result.usage_metadata.get('input_tokens', 0),
                        'output_tokens': result.usage_metadata.get('output_tokens', 0),
                        'total_tokens': result.usage_metadata.get('total_tokens', 0)
                    }
                
                # Log execution
                tracker.log_tool_execution(
                    tool_name, inputs, result, execution_time, tokens_used
                )
                
                logging.info(f"Tool completed: {tool_name} in {execution_time:.2f}s")
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_result = {'error': str(e)}
                
                tracker.log_tool_execution(
                    tool_name, inputs, error_result, execution_time
                )
                
                logging.error(f"Tool failed: {tool_name} - {e}")
                raise
        
        return wrapper
    return decorator