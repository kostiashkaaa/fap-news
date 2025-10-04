# Quick Start Guide

Get FAP News running in 5 minutes! 🚀

## Prerequisites

- Python 3.11+ installed
- Telegram account
- 5 minutes of your time

## Step 1: Get Telegram Bot Token

1. Open Telegram, search for [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Choose a name and username for your bot
4. **Copy the token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Get Your User ID

1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Send `/start`
3. **Copy your user ID** (a number like: `123456789`)

## Step 3: Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/fap-news.git
cd fap-news

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Run setup (will guide you through configuration)
python setup.py
```

The setup script will ask you for:
- Bot token (from Step 1)
- Your user ID (from Step 2)
- Groq API key (optional - press Enter to skip)

## Step 4: Create Telegram Channel

1. Create a new channel in Telegram
2. Make it public or get the chat ID
3. Add your bot as administrator with "Post Messages" permission

## Step 5: Configure Channel

Edit `config.json` and update:

```json
{
  "telegram": {
    "token": "your_token_here",
    "channel_id": "@your_channel"  // or "-100123456789"
  }
}
```

## Step 6: Run Bot

```bash
python bot.py
```

You should see:
```
INFO: Collecting news from 17 sources
INFO: Collected 45 items from RSS sources
INFO: Adding 3 new items to posting queue
```

## Step 7 (Optional): Enable AI Features

For better summaries, get free Groq API key:

1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up (free)
3. Create API key
4. Add to `.env`:
   ```
   GROQ_API_KEY=your_groq_key_here
   ```

## That's it! 🎉

Your bot is now:
- ✅ Collecting news from 17 international sources
- ✅ Filtering by keywords
- ✅ Posting to your channel every 1-4 minutes
- ✅ Avoiding duplicates

## Next Steps

### Add More Sources

```bash
# Start admin bot
python admin_bot.py

# Send /admin to your bot in Telegram
# Click "📰 Manage Sources"
# Click "➕ Add Source"
```

### Customize Filters

Edit `config.json`:

```json
{
  "filters": {
    "include_keywords": ["your", "topics"],
    "exclude_keywords": ["unwanted", "topics"],
    "max_age_hours": 24
  }
}
```

### Run 24/7

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- VPS deployment
- Docker setup
- Systemd service
- Auto-restart on failure

## Troubleshooting

### Bot not starting?
```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt
```

### Not posting to channel?
1. ✅ Bot is admin in channel?
2. ✅ Channel ID correct in config.json?
3. ✅ Check logs for errors

### Need help?
- 📖 [Full Documentation](README.md)
- ❓ [FAQ](FAQ.md)
- 🐛 [Report Issue](https://github.com/yourusername/fap-news/issues)

## Commands Cheat Sheet

```bash
# Start main bot
python bot.py

# Start admin bot
python admin_bot.py

# Run both at once
python run_all.py

# Update bot
git pull origin main
pip install -r requirements.txt --upgrade

# View logs (if using systemd)
sudo journalctl -u fap-news -f
```

## Configuration Cheat Sheet

### Minimal Config (RSS only, no AI)

```json
{
  "telegram": {
    "token": "YOUR_TOKEN",
    "channel_id": "@channel"
  },
  "ai_summarization": {
    "enabled": false
  }
}
```

### Full Config (AI enabled)

```json
{
  "telegram": {
    "token": "YOUR_TOKEN",
    "channel_id": "@channel"
  },
  "ai_summarization": {
    "enabled": true,
    "api_key": "YOUR_GROQ_KEY"
  },
  "filters": {
    "include_keywords": ["Ukraine", "Russia", "USA"],
    "max_age_hours": 24
  }
}
```

---

**Ready to customize?** Check out [README.md](README.md) for full documentation!

**Having issues?** See [FAQ.md](FAQ.md) for common questions!

**Want to contribute?** Read [CONTRIBUTING.md](CONTRIBUTING.md)!
