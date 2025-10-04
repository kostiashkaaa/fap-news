# Deployment Guide

This guide covers different ways to deploy FAP News bot.

## Table of Contents

- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [VPS Deployment](#vps-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring](#monitoring)

## Local Deployment

### Windows

```powershell
# 1. Clone repository
git clone https://github.com/yourusername/fap-news.git
cd fap-news

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup configuration
python setup.py

# 5. Run bot
python bot.py
```

### Linux/macOS

```bash
# 1. Clone repository
git clone https://github.com/yourusername/fap-news.git
cd fap-news

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup configuration
python setup.py

# 5. Run bot
python bot.py
```

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Create `.env` file:**
```bash
cp env.example.txt .env
# Edit .env with your credentials
```

2. **Create `config.json`:**
```bash
cp config.example.json config.json
# Edit config.json with your settings
```

3. **Start services:**
```bash
docker-compose up -d
```

4. **View logs:**
```bash
docker-compose logs -f
```

5. **Stop services:**
```bash
docker-compose down
```

### Using Docker Only

```bash
# Build image
docker build -t fap-news .

# Run main bot
docker run -d \
  --name fap-news-bot \
  --restart unless-stopped \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/data:/app/data \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e GROQ_API_KEY=your_key \
  fap-news python bot.py

# Run admin bot
docker run -d \
  --name fap-news-admin \
  --restart unless-stopped \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/data:/app/data \
  -e TELEGRAM_BOT_TOKEN=your_token \
  fap-news python admin_bot.py
```

## VPS Deployment

### Ubuntu/Debian Server

1. **Connect to your VPS:**
```bash
ssh user@your-vps-ip
```

2. **Install dependencies:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv git -y
```

3. **Clone and setup:**
```bash
git clone https://github.com/yourusername/fap-news.git
cd fap-news
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup.py
```

4. **Create systemd service:**

Create `/etc/systemd/system/fap-news.service`:

```ini
[Unit]
Description=FAP News Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/fap-news
Environment="PATH=/home/your-username/fap-news/.venv/bin"
ExecStart=/home/your-username/fap-news/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/fap-news-admin.service`:

```ini
[Unit]
Description=FAP News Admin Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/fap-news
Environment="PATH=/home/your-username/fap-news/.venv/bin"
ExecStart=/home/your-username/fap-news/.venv/bin/python admin_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

5. **Start services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable fap-news
sudo systemctl enable fap-news-admin
sudo systemctl start fap-news
sudo systemctl start fap-news-admin
```

6. **Check status:**
```bash
sudo systemctl status fap-news
sudo systemctl status fap-news-admin
```

7. **View logs:**
```bash
sudo journalctl -u fap-news -f
sudo journalctl -u fap-news-admin -f
```

## Cloud Deployment

### Heroku

1. **Install Heroku CLI**

2. **Create Procfile:**
```
worker: python bot.py
admin: python admin_bot.py
```

3. **Deploy:**
```bash
heroku create your-app-name
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set GROQ_API_KEY=your_key
git push heroku main
heroku ps:scale worker=1 admin=1
```

### Railway

1. Create new project on [Railway](https://railway.app/)
2. Connect GitHub repository
3. Add environment variables
4. Deploy automatically

### AWS EC2

Similar to VPS deployment above, but:
1. Use AWS Security Groups to allow HTTPS (443)
2. Use AWS Systems Manager for secure credential storage
3. Consider using AWS RDS for database (if scaling)

## Monitoring

### Basic Monitoring

**Check if bot is running:**
```bash
# Linux
ps aux | grep bot.py

# Docker
docker ps
```

**View logs:**
```bash
# Systemd
sudo journalctl -u fap-news -n 100

# Docker
docker logs fap-news-bot --tail 100
```

### Advanced Monitoring

**Using PM2 (Process Manager):**

```bash
# Install PM2
npm install -g pm2

# Start bot with PM2
pm2 start bot.py --name fap-news --interpreter python3
pm2 start admin_bot.py --name fap-news-admin --interpreter python3

# Monitor
pm2 status
pm2 logs

# Auto-start on reboot
pm2 startup
pm2 save
```

**Monitoring Checklist:**
- [ ] Bot process is running
- [ ] Logs show no errors
- [ ] News are being collected
- [ ] Posts appear in channel
- [ ] Database is growing
- [ ] Disk space is sufficient
- [ ] API rate limits not exceeded

## Backup

### What to Backup

1. **Configuration:**
   - `config.json`
   - `.env`

2. **Database:**
   - `fap_news.sqlite3`
   - `ai_cache.sqlite3`

### Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp config.json "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"

# Backup databases
cp *.sqlite3 "$BACKUP_DIR/"

# Compress
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup created: $BACKUP_DIR.tar.gz"

# Keep only last 7 backups
ls -t backups/*.tar.gz | tail -n +8 | xargs rm -f
```

Run daily with cron:
```bash
crontab -e
# Add: 0 2 * * * /path/to/fap-news/backup.sh
```

## Troubleshooting

### Bot not starting

1. Check Python version: `python --version`
2. Check dependencies: `pip list`
3. Verify credentials in `.env`
4. Check logs for errors

### Not posting to channel

1. Verify bot is admin in channel
2. Check channel ID is correct
3. Test bot token: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### High memory usage

1. Reduce `max_freshness_checks` in config
2. Clear AI cache: `rm ai_cache.sqlite3`
3. Restart bot regularly

### Rate limiting

1. Increase `delay_between_calls` in config
2. Reduce number of sources
3. Use caching (`cache_enabled: true`)

## Updates

### Manual Update

```bash
git pull origin main
pip install -r requirements.txt --upgrade
sudo systemctl restart fap-news
sudo systemctl restart fap-news-admin
```

### Automatic Updates

Create `update.sh`:

```bash
#!/bin/bash
cd /path/to/fap-news
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart fap-news
sudo systemctl restart fap-news-admin
echo "Updated successfully"
```

## Security Best Practices

1. ✅ Never commit `.env` or `config.json` with real credentials
2. ✅ Use environment variables for secrets
3. ✅ Keep Python and dependencies updated
4. ✅ Restrict SSH access (use SSH keys)
5. ✅ Enable firewall (UFW on Ubuntu)
6. ✅ Regular backups
7. ✅ Monitor logs for suspicious activity
8. ✅ Use HTTPS for all API calls

## Performance Tips

1. **Optimize source count:** Start with 5-10 sources
2. **Adjust intervals:** Increase `interval_minutes` to 15-30
3. **Enable caching:** Set `cache_enabled: true`
4. **Use priorities:** Set priorities for important sources
5. **Limit AI calls:** Reduce `max_freshness_checks`

## Support

- 📖 [Documentation](README.md)
- 🐛 [Report Issues](https://github.com/yourusername/fap-news/issues)
- 💬 [Discussions](https://github.com/yourusername/fap-news/discussions)

---

Last updated: 2025-01-16
