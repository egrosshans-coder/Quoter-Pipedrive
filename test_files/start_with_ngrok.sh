#!/bin/bash
# Start Cover Letter Editor with Public URL

echo "🚀 Starting Cover Letter Editor with Public Access..."
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Installing..."
    brew install ngrok/ngrok/ngrok
fi

# Start the editor in background
echo "📝 Starting cover letter editor..."
source venv/bin/activate
python cover_letter_editor.py &
EDITOR_PID=$!

# Wait a moment for server to start
sleep 3

# Start ngrok tunnel
echo "🌐 Creating public tunnel..."
ngrok http 5001 --log=stdout > ngrok.log &
NGROK_PID=$!

# Wait for ngrok to start
sleep 5

# Get the public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')

echo ""
echo "✅ Cover Letter Editor is now live!"
echo "📝 Public URL: $PUBLIC_URL"
echo ""
echo "🎯 Share this URL with your sales team:"
echo "   $PUBLIC_URL"
echo ""
echo "⚠️  Keep this terminal open while team is using the editor"
echo "🛑 Press Ctrl+C to stop both services"

# Wait for user to stop
wait
