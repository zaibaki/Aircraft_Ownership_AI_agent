# Aircraft Ownership Intelligence Agent

An AI-powered research system that identifies real decision-makers behind private aircraft ownership using LangGraph and multiple data sources.

## Features

- **Multi-source Data Integration**: FAA registry, OpenCorporates, contact enrichment APIs
- **Intelligent Analysis**: Identifies shell companies, trusts, and corporate structures
- **Contact Discovery**: Finds decision-makers with email, phone, LinkedIn profiles
- **Confidence Scoring**: Provides reliability assessment with justification
- **Human-in-the-Loop**: Escalates complex cases to expert review
- **Memory & Tracing**: Persistent conversations with LangSmith observability

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export LANGSMITH_API_KEY="your-langsmith-key"
   export TAVILY_API_KEY="your-tavily-key"
   export LANGSMITH_TRACING="true"
   ```

3. **Run Single Query**:
   ```bash
   python main.py N123AB
   ```

4. **Interactive Mode**:
   ```bash
   python main.py --interactive
   ```

## Architecture

```
aircraft_ownership_agent/
├── config/          # Settings and prompts
├── data/           # FAA database and cache
├── tools/          # Data source integrations
├── agents/         # LangGraph nodes and state
├── parsers/        # Data extraction logic
├── utils/          # Shared utilities
└── main.py         # CLI interface
```

## Key Tools

- `faa_database_lookup`: Local FAA registry search
- `faa_web_scraper`: Real-time FAA data
- `opencorporates_search`: Corporate entity research
- `contact_enrichment`: Decision-maker identification
- `human_assistance`: Expert escalation

## Output Example

```
🛩️ AIRCRAFT INFORMATION:
   Tail Number: N123AB
   Manufacturer: BOMBARDIER INC
   Model: BD-700-1A10

👥 OWNERSHIP STRUCTURE:
   Registered Owner: TVPX ARS INC TRUSTEE
   Entity Type: Trust

🏢 CORPORATE ENTITIES (2 found):
   1. 🔥 TVPX AIRCRAFT SOLUTIONS INC (Score: 85%)

📊 CONFIDENCE ASSESSMENT: ✅ 75%
```
Usage Examples:
bash# Single lookup
python main.py N123AB

# Interactive mode
python main.py --interactive

# Save results
python main.py N123AB --save results.json


This system is designed for private aviation professionals who need fast, reliable intelligence on aircraft ownership structures and decision-makers.