#!/bin/bash

# Installation script for CAM export packages
# This installs optional packages for PDF and Word export functionality

echo "=========================================="
echo "CAM Export Packages Installation"
echo "=========================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "It's recommended to activate your virtual environment first:"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Installing packages..."
echo ""

# Install markdown (for HTML conversion)
echo "📦 Installing markdown..."
pip install markdown

# Install weasyprint (for PDF export)
echo "📦 Installing weasyprint (PDF export)..."
pip install weasyprint

# Install python-docx (for Word export)
echo "📦 Installing python-docx (Word export)..."
pip install python-docx

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Installed packages:"
echo "  - markdown (HTML conversion)"
echo "  - weasyprint (PDF export)"
echo "  - python-docx (Word export)"
echo ""
echo "You can now export CAMs to PDF and Word formats."
echo ""
echo "To test:"
echo "  1. Start the backend server: uvicorn app.main:app --reload"
echo "  2. Navigate to an application's CAM tab"
echo "  3. Click 'Export PDF' or 'Export Word'"
echo ""
