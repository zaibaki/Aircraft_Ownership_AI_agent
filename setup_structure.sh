#!/bin/bash

# Top-level files
touch main.py requirements.txt README.md

# Config
mkdir -p config
touch config/__init__.py config/settings.py

# Agent
mkdir -p agent
touch agent/__init__.py agent/graph.py agent/prompts.py

# Tools
mkdir -p tools
touch tools/__init__.py \
      tools/base.py \
      tools/faa_scraper.py \
      tools/flightaware_scraper.py \
      tools/tavily_search.py \
      tools/ownership_analyzer.py

# Models
mkdir -p models
touch models/__init__.py models/schemas.py

# Utils
mkdir -p utils
touch utils/__init__.py \
      utils/logging_config.py \
      utils/web_utils.py

# Tests
mkdir -p tests
touch tests/__init__.py \
      tests/test_tools.py \
      tests/test_agent.py

echo "✅ Project structure for aircraft_research_agent created successfully!"
