#!/bin/bash
# Quick script to check if test data generation is progressing

echo "Checking test data generation progress..."
echo ""

# Check if pytest process is running
if pgrep -f "pytest.*test_generate_test_data" > /dev/null; then
    echo "✅ pytest process is running"
    PID=$(pgrep -f "pytest.*test_generate_test_data" | head -1)
    echo "   PID: $PID"
    
    # Check CPU usage
    if command -v ps > /dev/null; then
        CPU=$(ps -p $PID -o %cpu= 2>/dev/null | tr -d ' ')
        echo "   CPU usage: ${CPU}%"
    fi
    
    # Check if it's writing files
    if [ -d "tests/fixtures" ]; then
        TRANSCRIPT_COUNT=$(find tests/fixtures/sample_transcripts -name "*.txt" 2>/dev/null | wc -l | tr -d ' ')
        WRITING_COUNT=$(find tests/fixtures/sample_writing -name "*.txt" 2>/dev/null | wc -l | tr -d ' ')
        PROFILE_COUNT=$(find tests/fixtures/student_profiles -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
        
        echo ""
        echo "📁 Files generated so far:"
        echo "   Transcripts: $TRANSCRIPT_COUNT / 54"
        echo "   Writing samples: $WRITING_COUNT / 27"
        echo "   Profiles: $PROFILE_COUNT / 30"
        
        if [ "$TRANSCRIPT_COUNT" -gt 0 ] || [ "$WRITING_COUNT" -gt 0 ] || [ "$PROFILE_COUNT" -gt 0 ]; then
            echo ""
            echo "✅ Progress detected - test is likely still running"
        else
            echo ""
            echo "⚠️  No files generated yet - may be stuck at start"
        fi
    else
        echo ""
        echo "⚠️  tests/fixtures directory doesn't exist yet"
    fi
else
    echo "❌ pytest process not found"
    echo "   Test may have completed or crashed"
fi

echo ""
echo "To see live output, run:"
echo "  tail -f /tmp/pytest_output.log  # if redirected"
echo "  or check the terminal where pytest is running"

