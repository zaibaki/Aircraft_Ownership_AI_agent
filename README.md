# Aircraft Ownership Research Agent

A sophisticated AI-powered agent built with LangGraph that researches aircraft ownership information using multiple data sources.

## Features

- **FAA Registry Scraping**: Extracts official aircraft registration data
- **FlightAware Integration**: Gathers operational and ownership data
- **Web Search**: Finds additional ownership and contact information using Tavily
- **Ownership Analysis**: Identifies decision makers and analyzes business entities
- **LangSmith Observability**: Full tracing and monitoring
- **Modular Architecture**: Clean separation of concerns with comprehensive logging

## Quick Start

### 1. Installation

```bash
git clone <repository>
cd aircraft_research_agent
pip install -r requirements.txt
```

### 2. Environment Setup

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **OpenAI API Key**: For the LLM (GPT-4o-mini)
- **Tavily API Key**: For web search capabilities
- **LangSmith API Key**: For observability (optional but recommended)

### 3. Run the Demo

```bash
python main.py
```

## Architecture

### Directory Structure

```
aircraft_research_agent/
├── main.py                    # Entry point and demo
├── config/settings.py         # Configuration management
├── agent/                     # LangGraph agent implementation
├── tools/                     # Individual research tools
├── models/schemas.py          # Data models
├── utils/                     # Utilities and logging
└── tests/                     # Test suite
```

### Tools Overview

1. **FAA Registration Scraper**
   - Scrapes official FAA aircraft registry
   - Extracts owner, manufacturer, model details
   - URL: `https://registry.faa.gov/AircraftInquiry/Search/NNumberResult`

2. **FlightAware Scraper** 
   - Gathers operational data and additional owner info
   - Uses Selenium for dynamic content
   - URL: `https://www.flightaware.com/resources/registration/`

3. **Tavily Ownership Search**
   - Web search for additional ownership information
   - Extracts contact details (email, phone, LinkedIn)
   - Searches for business entity information

4. **Ownership Analyzer**
   - Analyzes data from multiple sources
   - Identifies likely decision makers
   - Calculates confidence scores
   - Determines business entity types

## Usage Examples

### Basic Research

```python
from agent.graph import AircraftResearchAgent

agent = AircraftResearchAgent()
result = agent.research_aircraft("N540JT")
```

### Custom Thread ID

```python
result = agent.research_aircraft("N540JT", thread_id="custom_session")
```

### Using Different OpenAI Models

```python
# Using GPT-4 (more expensive but potentially better)
agent = AircraftResearchAgent(model_name="openai:gpt-4")

# Using GPT-4o-mini (default, cost-effective)
agent = AircraftResearchAgent(model_name="openai:gpt-4o-mini")

# Using GPT-3.5 Turbo (fastest, most economical)
agent = AircraftResearchAgent(model_name="openai:gpt-3.5-turbo")
```

## Configuration

### Environment Variables

- `LANGSMITH_API_KEY`: LangSmith API key for tracing
- `LANGSMITH_TRACING`: Enable/disable tracing (default: true)
- `LANGSMITH_PROJECT`: Project name for traces
- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `TAVILY_API_KEY`: Tavily API key for web search

### Logging

Logs are written to both console and `aircraft_research.log` file. Log levels can be configured in the logging setup.

## Data Sources

### Primary Sources
- **FAA Aircraft Registry**: Official US aircraft registration database
- **FlightAware**: Aviation data and aircraft tracking platform

### Secondary Sources
- **Web Search (Tavily)**: General web search for ownership details
- **Business Registries**: Company information and contacts

## Output Format

The agent returns comprehensive research results including:

```json
{
  "n_number": "N540JT",
  "aircraft_details": {
    "manufacturer": "Cessna",
    "model": "Citation",
    "year": "2015"
  },
  "ownership_info": {
    "primary_owner": "ACME Aviation LLC",
    "decision_maker": "John Smith",
    "role": "CEO",
    "email": "john@acmeaviation.com",
    "phone": "555-123-4567",
    "linkedin": "linkedin.com/in/johnsmith",
    "company_type": "LLC",
    "confidence_score": 0.85
  },
  "evidence_links": [
    "https://registry.faa.gov/...",
    "https://acmeaviation.com/about"
  ]
}
```

## Testing

Run the test suite:

```bash
pytest tests/
```

## Development

### Adding New Tools

1. Create a new tool class inheriting from `BaseResearchTool`
2. Implement the `_run` method
3. Add appropriate logging and error handling
4. Register the tool in the agent configuration

### Example Tool Structure

```python
from tools.base import BaseResearchTool

class CustomTool(BaseResearchTool):
    name = "custom_tool"
    description = "Tool description for the LLM"
    
    def _run(self, input_param: str) -> Dict[str, Any]:
        self._log_tool_start({"input_param": input_param})
        
        try:
            # Tool implementation
            result = self.process_data(input_param)
            self._log_tool_end(result)
            return result
        except Exception as e:
            self._log_error(e, {"input_param": input_param})
            return {"error": str(e)}
```

## Cost Considerations

### OpenAI Model Costs (approximate per 1K tokens)
- **GPT-4**: ~$0.03 input, ~$0.06 output (highest quality)
- **GPT-4o-mini**: ~$0.00015 input, ~$0.0006 output (recommended default)
- **GPT-3.5 Turbo**: ~$0.0005 input, ~$0.0015 output (most economical)

A typical aircraft research session uses 2,000-5,000 tokens, making GPT-4o-mini very cost-effective for this use case.

## Limitations

- Currently US-only aircraft support
- Requires stable internet connection for web scraping
- Rate limits apply to external APIs
- Some aircraft may have limited public information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add appropriate license]

## Support

For issues and questions:
1. Check the logs in `aircraft_research.log`
2. Verify API keys are correctly configured
3. Ensure all dependencies are installed
4. Check LangSmith traces for debugging

## Roadmap

- [ ] Support for international aircraft registries
- [ ] Enhanced entity resolution algorithms
- [ ] Real-time data caching
- [ ] API endpoint for integration
- [ ] Enhanced contact information validation
- [ ] Support for corporate hierarchy analysis