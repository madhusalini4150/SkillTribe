#!/bin/bash
echo "🚀 Starting SkillTribe..."
echo ""
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q
echo ""
echo "✅ SkillTribe is running at http://localhost:5000"
echo "   Demo login: demo@demo.com / demo1234"
echo ""
python app.py
