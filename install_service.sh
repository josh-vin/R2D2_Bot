#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root or with sudo${NC}"
  exit 1
fi

# Get username who invoked sudo
if [ -n "$SUDO_USER" ]; then
  ACTUAL_USER=$SUDO_USER
else
  ACTUAL_USER=$(whoami)
fi

# Get home directory of actual user
USER_HOME=$(getent passwd $ACTUAL_USER | cut -d: -f6)

echo -e "${YELLOW}Installing R2D2 SWGOH Bot as systemd service${NC}"
echo "=================================================="

# Update the service file with correct username
echo "Configuring service file with username: $ACTUAL_USER"
sed -i "s|your_linux_username|$ACTUAL_USER|g" $USER_HOME/R2D2_Bot/r2d2bot.service

# Copy service file to systemd directory
echo "Installing systemd service..."
cp $USER_HOME/R2D2_Bot/r2d2bot.service /etc/systemd/system/

# Set file ownership
echo "Setting file ownership..."
chown -R $ACTUAL_USER:$ACTUAL_USER $USER_HOME/R2D2_Bot

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting service..."
systemctl enable r2d2bot
systemctl start r2d2bot

# Check service status
echo -e "\n${YELLOW}Service Status${NC}"
systemctl status r2d2bot

echo -e "\n${GREEN}Installation complete!${NC}"
echo "To check bot status: sudo systemctl status r2d2bot"
echo "To view logs: sudo journalctl -u r2d2bot -f"
echo "To stop bot: sudo systemctl stop r2d2bot"
echo "To start bot: sudo systemctl start r2d2bot"
echo "To restart bot: sudo systemctl restart r2d2bot"
