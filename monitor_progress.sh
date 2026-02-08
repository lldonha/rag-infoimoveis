#!/bin/bash
# Real-time progress monitor for 1000 properties scraping

echo "=================================="
echo "🏠 InfoImóveis 1000 Properties Monitor"
echo "=================================="
echo ""
echo "Started: $(date)"
echo ""

TARGET=1000
CHECK_INTERVAL=300  # Check every 5 minutes

while true; do
    COUNT=$(ls -1 .tmp/batch_1000_imoveis/property_*/data.json 2>/dev/null | wc -l)
    PERCENT=$(echo "scale=1; $COUNT * 100 / $TARGET" | bc -l 2>/dev/null || echo "0")
    
    # Calculate ETA
    if [ $COUNT -gt 0 ]; then
        # Roughly 3 properties per minute observed
        REMAINING=$(( (TARGET - COUNT) / 3 ))
        HOURS=$((REMAINING / 60))
        MINUTES=$((REMAINING % 60))
        ETA="${HOURS}h ${MINUTES}m"
    else
        ETA="Calculating..."
    fi
    
    clear
    echo "=================================="
    echo "🏠 InfoImóveis 1000 Properties Monitor"
    echo "=================================="
    echo ""
    echo "📊 Progress: $COUNT/$TARGET properties ($PERCENT%)"
    echo "⏱️  ETA: $ETA"
    echo ""
    
    # Progress bar
    BAR_WIDTH=50
    FILLED=$((COUNT * BAR_WIDTH / TARGET))
    EMPTY=$((BAR_WIDTH - FILLED))
    
    printf "["
    printf "%${FILLED}s" | tr ' ' '█'
    printf "%${EMPTY}s" | tr ' ' '░'
    printf "]\n"
    
    echo ""
    echo "Last check: $(date)"
    echo "Press Ctrl+C to exit"
    echo ""
    
    # Show recent log entries
    if [ -f ".tmp/auto_complete.log" ]; then
        echo "Recent activity:"
        tail -3 .tmp/auto_complete.log 2>/dev/null
    fi
    
    # Exit if complete
    if [ $COUNT -ge $TARGET ]; then
        echo ""
        echo "🎉 SCRAPING COMPLETE! 🎉"
        echo ""
        echo "Next steps:"
        echo "  1. AI Analysis will start automatically"
        echo "  2. Excel will be generated"
        echo "  3. GitHub commit will be made"
        break
    fi
    
    sleep $CHECK_INTERVAL
done
