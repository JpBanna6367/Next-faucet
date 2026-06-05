#!/bin/bash
echo "Starting NextFaucet Bot on Render..."
echo "Working directory: $(pwd)"
ls -la

# Install dependencies
pip install -r requirements.txt

# Run bot with auto cookie from env
python3 nextfaucet.py
