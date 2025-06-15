# R2D2 SWGOH Bot - Linux Setup Guide

This guide covers how to set up the R2D2 SWGOH Discord Bot on a Linux server as a systemd service.

## Quick Start

1. **Transfer files to your Linux server**

2. **Make scripts executable**
   ```bash
   chmod +x setup_linux.sh install_service.sh status.sh
   ```

3. **Run the setup script**
   ```bash
   ./setup_linux.sh
   ```

4. **Install as a systemd service**
   ```bash
   sudo ./install_service.sh
   ```

That's it! Your bot should now be running as a systemd service.

---

## What Each Script Does

### setup_linux.sh
- Installs required system packages
- Creates directory structure
- Sets up Python virtual environment
- Installs Python dependencies from requirements.txt

### install_service.sh
- Configures systemd service file with your username
- Installs the service
- Enables it to start on boot
- Starts the service

### status.sh
- Shows if the bot is running
- Displays basic system resource usage
- Shows recent errors (if any)

---

## Common Commands

### Check service status
```bash
sudo systemctl status r2d2bot
```

### View logs
```bash
sudo journalctl -u r2d2bot -f
```

### Restart the service
```bash
sudo systemctl restart r2d2bot
```

### Stop the service
```bash
sudo systemctl stop r2d2bot
```

---

## Troubleshooting

### Bot not starting
Check the logs for errors:
```bash
sudo journalctl -u r2d2bot -e
```

### Updating the bot later
If you need to update your bot files:
1. Copy new files to ~/R2D2_Bot/
2. Restart the service:
   ```bash
   sudo systemctl restart r2d2bot
   ```

### Issues with requirements
If you need to update Python packages:
```bash
cd ~/R2D2_Bot
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart r2d2bot
```

---

## File Locations

- **Bot files**: ~/R2D2_Bot/
- **Virtual environment**: ~/R2D2_Bot/venv/
- **Service file**: /etc/systemd/system/r2d2bot.service
- **Logs**: Access with `sudo journalctl -u r2d2bot`

---

*Created on June 15, 2025*
