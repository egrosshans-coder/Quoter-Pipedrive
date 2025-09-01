#!/bin/bash

# Summary Generation Script
# Automates the execution of progress_summary_generator.py

echo "🚀 Starting Summary Generation Process..."

# Check if the Python script exists
if [ ! -f "progress_summary_generator.py" ]; then
    echo "❌ Error: progress_summary_generator.py not found!"
    echo "   Make sure you're in the correct directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Python virtual environment (venv) not found!"
    echo "   Please create the virtual environment first."
    exit 1
fi

echo "✅ Found progress_summary_generator.py"
echo "✅ Found virtual environment"

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Run the summary generator
echo "📊 Running progress summary generator..."
python progress_summary_generator.py

# Check exit status
if [ $? -eq 0 ]; then
    echo "✅ Summary generation completed successfully!"
    echo "📁 Check the work_logs/ folder for generated summaries"
else
    echo "❌ Summary generation failed!"
fi

# Deactivate virtual environment
echo "🔄 Deactivating virtual environment..."
deactivate

echo "🏁 Summary generation process completed!"
