#!/bin/bash
# Start Cover Letter Editor for Team Access

echo "🚀 Starting Cover Letter Editor for Team Access..."
echo "📝 The editor will be accessible at:"
echo "   Local: http://localhost:5001"
echo "   Network: http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "🎯 Share the network URL with your sales team!"
echo "⚠️  Keep this terminal open while team is using the editor"
echo ""

# Activate virtual environment and start server
source venv/bin/activate
python cover_letter_editor.py
