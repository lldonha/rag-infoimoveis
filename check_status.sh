#!/bin/bash
# Quick status checker for 1000 properties workflow

echo "=================================="
echo "📊 InfoImóveis 1000 Properties Status"
echo "=================================="
echo ""

# Count processed properties
COUNT=$(ls -1 .tmp/batch_1000_imoveis/property_*/data.json 2>/dev/null | wc -l)
PERCENT=$(echo "scale=1; $COUNT / 10" | bc -l 2>/dev/null || echo "0")

echo "Progress: $COUNT/1000 properties ($PERCENT%)"
echo ""

# Show progress bar
BAR_WIDTH=50
FILLED=$((COUNT * BAR_WIDTH / 1000))
EMPTY=$((BAR_WIDTH - FILLED))

printf "["
printf "%${FILLED}s" | tr ' ' '█'
printf "%${EMPTY}s" | tr ' ' '░'
printf "]\n"
echo ""

# Check if auto-complete is running
if [ -f ".tmp/auto_complete.log" ]; then
    echo "📋 Last 5 log entries:"
    tail -5 .tmp/auto_complete.log 2>/dev/null
    echo ""
fi

# Estimated time remaining
if [ $COUNT -gt 0 ]; then
    # Rough estimate: 20 seconds per property
    REMAINING=$(( (1000 - COUNT) * 20 ))
    HOURS=$((REMAINING / 3600))
    MINUTES=$(((REMAINING % 3600) / 60))
    echo "⏱️  Estimated time remaining: ${HOURS}h ${MINUTES}m"
fi

echo ""
echo "=================================="
echo "To check again, run: ./check_status.sh"
