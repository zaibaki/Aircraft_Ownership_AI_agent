# tools/tavily_search.py
from typing import Dict, Any, List
from langchain_tavily import TavilySearch
from tools.base import BaseResearchTool
from pydantic import Field

class TavilyOwnershipSearch(BaseResearchTool):
    """Tool to search for additional ownership information using Tavily."""
    
    name: str = Field(default="tavily_ownership_search", description="Tavily Ownership Search")
    description: str = Field(default="""
    Searches the web for additional aircraft ownership information using Tavily.
    Input: search_query (string containing aircraft info, owner name, or company name)
    Returns: Web search results with relevant ownership and contact information.
    """)
    
    def __init__(self, max_results: int = 5):
        super().__init__()
        self.tavily = TavilySearch(max_results=max_results)
    
    def _run(self, search_query: str) -> Dict[str, Any]:
        """Execute the Tavily search."""
        try:
            self._log_tool_start({"search_query": search_query})
            
            # Perform the search
            results = self.tavily.invoke(search_query)
            
            # Process and enhance results
            processed_results = self._process_search_results(results, search_query)
            
            self._log_tool_end(processed_results)
            return processed_results
            
        except Exception as e:
            self._log_error(e, {"search_query": search_query})
            return {"error": str(e), "search_query": search_query}
    
    def _process_search_results(self, results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Process and enhance Tavily search results."""
        processed = {
            "search_query": query,
            "source": "Tavily Search",
            "results": []
        }
        
        try:
            if isinstance(results, dict) and 'results' in results:
                for result in results['results']:
                    processed_result = {
                        "title": result.get('title', ''),
                        "url": result.get('url', ''),
                        "content": result.get('content', ''),
                        "score": result.get('score', 0)
                    }
                    
                    # Extract potential contact information
                    content_lower = result.get('content', '').lower()
                    
                    # Look for email patterns
                    import re
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                                      result.get('content', ''))
                    if emails:
                        processed_result['emails'] = emails
                    
                    # Look for phone patterns
                    phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 
                                      result.get('content', ''))
                    if phones:
                        processed_result['phones'] = phones
                    
                    # Look for LinkedIn profiles
                    if 'linkedin.com' in result.get('url', '').lower():
                        processed_result['linkedin_profile'] = True
                    
                    processed['results'].append(processed_result)
            
            self.logger.info(f"Processed {len(processed['results'])} search results")
            return processed
            
        except Exception as e:
            self.logger.warning(f"Error processing search results: {str(e)}")
            processed['process_error'] = str(e)
            return processed
