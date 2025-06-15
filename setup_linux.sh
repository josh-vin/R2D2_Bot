#!/bin/bash

# R2D2 SWGOH Bot Linux Deployment Script

# Check if python3-venv is installed
if ! dpkg -l | grep -q python3-venv; then
    echo "python3-venv is not installed. Attempting to install..."
    sudo apt update
    sudo apt install -y python3-venv python3-full
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p ~/R2D2_Bot/mod_images

# Copy files
echo "Copying files..."
cp -r ./* ~/R2D2_Bot/

# Setup virtual environment
echo "Setting up virtual environment..."
cd ~/R2D2_Bot
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set file permissions
echo "Setting file permissions..."
chmod 600 .env
chmod +x bot_swgoh.py

# Create log directory
mkdir -p logs

echo -e "\nSetup complete!"
echo -e "\nTo run the bot manually:"
echo "cd ~/R2D2_Bot"
echo "source venv/bin/activate"
echo "python bot_swgoh.py"
echo -e "\nTo set up as a systemd service, edit the r2d2bot.service file with your username"
echo "and copy it to /etc/systemd/system/, then run:"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable r2d2bot"
echo "sudo systemctl start r2d2bot"
