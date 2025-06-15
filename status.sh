#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}R2D2 SWGOH Bot Status${NC}"
echo "=========================="

# Check if process is running
if pgrep -f "python.*bot_swgoh.py" > /dev/null
then
    echo -e "${GREEN}Bot is running${NC}"
    # Get uptime of bot process
    pid=$(pgrep -f "python.*bot_swgoh.py")
    start_time=$(ps -o lstart= -p $pid)
    echo "Process ID: $pid"
    echo "Started: $start_time"
else
    echo -e "${RED}Bot is not running${NC}"
fi

# Check disk space
echo -e "\n${YELLOW}Disk Usage${NC}"
df -h | grep -E "Size|/$"

# Check memory usage
echo -e "\n${YELLOW}Memory Usage${NC}"
free -h

# Check for any error logs
if [ -d "logs" ]; then
    echo -e "\n${YELLOW}Recent Errors${NC}"
    grep -i "error\|exception\|failed" logs/* 2>/dev/null | tail -5
fi

echo -e "\n${YELLOW}Bot Commands${NC}"
echo "Start:  systemctl start r2d2bot"
echo "Stop:   systemctl stop r2d2bot"
echo "Status: systemctl status r2d2bot"
echo "Logs:   journalctl -u r2d2bot -f"
