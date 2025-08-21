#!/bin/bash

# Create top-level files
touch README.md requirements.txt main.py run_agent.py

# Create config folder and files
mkdir -p config
touch config/__init__.py config/settings.py config/prompts.py

# Create data folders and FAA DB files
mkdir -p data/faa_db data/cache
touch data/faa_db/MASTER.txt \
      data/faa_db/ACFTREF.txt \
      data/faa_db/ENGINE.txt \
      data/faa_db/DEALER.txt \
      data/faa_db/DEREG.txt \
      data/faa_db/DOCINDEX.txt \
      data/faa_db/RESERVED.txt

# Create tools folder and files
mkdir -p tools
touch tools/__init__.py \
      tools/faa_tools.py \
      tools/corporate_tools.py \
      tools/contact_tools.py \
      tools/flight_tools.py \
      tools/human_assistance.py

# Create agents folder and files
mkdir -p agents
touch agents/__init__.py \
      agents/state.py \
      agents/nodes.py \
      agents/graph.py

# Create parsers folder and files
mkdir -p parsers
touch parsers/__init__.py \
      parsers/faa_parser.py \
      parsers/corporate_parser.py \
      parsers/contact_parser.py

# Create utils folder and files
mkdir -p utils
touch utils/__init__.py \
      utils/cache_manager.py \
      utils/data_validator.py \
      utils/confidence_scorer.py

echo "✅ Project structure created successfully!"
