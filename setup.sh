#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Install requirements (from within virtual environment)
./venv/bin/pip install -r requirements.txt

echo ""
echo "Setup complete! Virtual environment created and packages installed."
echo "To activate the virtual environment, run: source venv/bin/activate"
