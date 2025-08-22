#!/bin/bash

# Top-level files
touch __init__.py main.py

# API
mkdir -p api
touch api/__init__.py api/routes.py

# Core
mkdir -p core
touch core/__init__.py core/config.py core/logging_config.py

# Services
mkdir -p services
touch services/__init__.py services/aircraft_service.py

# Templates
mkdir -p templates
touch templates/base.html templates/index.html templates/result.html

echo "✅ app/ structure created successfully!"
