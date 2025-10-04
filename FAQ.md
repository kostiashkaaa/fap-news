# Frequently Asked Questions (FAQ)

## General Questions

### What is FAP News?

FAP News is an intelligent Telegram bot that automatically collects, translates, and posts news from multiple international sources. It uses AI to create summaries, detect urgent news, and filter duplicates.

### Is it free to use?

Yes, FAP News is open source and free to use. However, you'll need:
- A free Telegram bot token
- (Optional) A free Groq API key for AI features

### What makes it different from other news bots?

- 🤖 **AI-powered**: Smart summarization, urgency detection, duplicate filtering
- 🌍 **Multi-source**: Aggregates from 15+ international news sources
- 🎯 **Smart filtering**: Keyword-based and importance-based filtering
- 📊 **Admin panel**: Easy management via Telegram
- 💾 **Caching**: Reduces API costs

## Setup Questions

### How do I get a Telegram bot token?

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Follow instructions to choose name and username
4. Copy the token provided

### How do I get my Telegram User ID?

1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Send `/start`
3. Copy your user ID from the response

### Do I need a Groq API key?

No, it's optional but highly recommended. Without it:
- No AI summarization (uses original content)
- No urgency detection
- No freshness analysis
- No adaptive summary lengths

Get a free key at [console.groq.com](https://console.groq.com/)

### Can I use it without AI features?

Yes! Set `"enabled": false` in the `ai_summarization` section of config.json. The bot will still:
- Collect news from sources
- Filter by keywords
- Post to your channel
- Deduplicate stories (non-AI method)

### How do I make my bot an admin in my channel?

1. Open your Telegram channel
2. Go to channel info → Administrators
3. Click "Add Administrator"
4. Search for your bot and add it
5. Give it "Post Messages" permission

## Configuration Questions

### What's the difference between `max_age_hours` and `max_age_minutes`?

- `max_age_hours`: Filters news by publication date (from RSS feed)
- `max_age_minutes`: AI analyzes if news mentions recent events

Use `max_age_minutes` for fresher news with AI enabled.

### How many news sources should I add?

Start with 5-10 sources. More sources = more API calls and longer processing time.

### What's the best posting interval?

- `interval_minutes: 10` - Check for news every 10 minutes (recommended)
- `min_delay_minutes: 1` - Minimum time between posts
- `max_delay_minutes: 4` - Maximum time between posts

This gives natural posting rhythm.

### How do I add a new RSS source?

Two ways:

**1. Via Admin Bot (easier):**
```
1. Start admin_bot.py
2. Send /admin
3. Click "📰 Manage Sources"
4. Click "➕ Add Source"
5. Follow prompts
```

**2. Via config.json:**
```json
{
  "name": "Source Name",
  "tag": "#tag",
  "rss": "https://example.com/rss",
  "priority": 1
}
```

## Usage Questions

### Why isn't my bot posting anything?

Check these:
1. ✅ Bot is running without errors
2. ✅ Bot is admin in channel
3. ✅ Sources are returning news
4. ✅ News matches your keyword filters
5. ✅ News hasn't been posted before
6. ✅ News isn't too old

View logs for details: `python bot.py` (console output)

### How do I test without posting to my real channel?

1. Create a test channel
2. Add bot as admin
3. Change `channel_id` in config.json to test channel
4. Run bot

### Can I use multiple channels?

Not directly, but you can:
1. Run multiple bot instances with different config files
2. Or modify the code to loop through channels

### How do I stop duplicate news?

The bot has smart deduplication enabled by default:

```json
"deduplication": {
  "enabled": true,
  "similarity_threshold": 0.7  // 0-1, higher = stricter
}
```

Increase threshold to filter more duplicates.

### How long are news summaries?

Depends on importance:
- **Critical news**: Up to 1200 characters
- **High importance**: Up to 900 characters
- **Medium**: 500 characters
- **Low**: 400 characters

Adjust `max_summary_length` in config.json for base length.

## Technical Questions

### What are the system requirements?

**Minimum:**
- Python 3.11+
- 256 MB RAM
- 1 GB disk space

**Recommended:**
- Python 3.11+
- 512 MB RAM
- 2 GB disk space
- VPS with 24/7 uptime

### How much does it cost to run?

**Free tier (recommended for starting):**
- Telegram: Free
- Groq API: 30 requests/minute free
- Hosting: $5-10/month VPS or free (local PC)

**If scaling:**
- Groq API: $0.10 per 1M tokens (very cheap)
- Better VPS: $10-20/month

### Can I run it on Windows?

Yes! Follow the Windows setup instructions in README.md.

### Can I run it on Raspberry Pi?

Yes, but:
- Use Raspberry Pi 4 (4GB RAM+)
- Install Python 3.11+
- Expect slower performance

### Does it work on shared hosting?

No, you need:
- Python 3.11+ support
- Ability to run long-running processes
- Terminal access

Use VPS instead.

### How much bandwidth does it use?

Approximately:
- 10-50 MB/day for RSS feeds
- 1-10 MB/day for API calls
- Total: ~20-100 MB/day

Very light!

### Where is data stored?

Two SQLite databases:
- `fap_news.sqlite3` - Published news tracking
- `ai_cache.sqlite3` - AI response cache

No external database needed.

## AI Questions

### Why use Groq instead of OpenAI?

- ⚡ Much faster (up to 10x)
- 💰 More generous free tier
- 🎯 Great for news summarization
- 🔄 Compatible API

You can modify code for other providers.

### How accurate are AI summaries?

Generally very good, but:
- ✅ Extracts key facts accurately
- ✅ Preserves important details
- ⚠️ May miss subtle nuances
- ⚠️ Rare translation errors

Review summaries initially to ensure quality.

### Can I use a different AI model?

Yes! Edit `ai_summarizer.py` to use:
- OpenAI GPT
- Anthropic Claude  
- Local models (Ollama)
- Any OpenAI-compatible API

### Does AI cache reduce quality?

No! Caching:
- ✅ Stores AI responses for identical news
- ✅ Reduces API costs
- ✅ Faster processing
- ✅ Maintains quality

Cache expires after 24 hours (configurable).

### What if AI API is down?

The bot will:
1. Try to use cached responses
2. Fall back to original content
3. Continue posting (no AI features)
4. Retry later

## Troubleshooting

### Error: "No module named 'aiogram'"

```bash
pip install -r requirements.txt
```

### Error: "Unauthorized" from Telegram

- Check bot token is correct
- Verify no extra spaces in token

### Error: Rate limit exceeded

Reduce API calls:
```json
"rate_limit": {
  "max_urgency_checks": 5,
  "max_freshness_checks": 8,
  "delay_between_calls": 1.0
}
```

### Bot posts old news

Reduce `max_age_hours` or enable AI freshness analysis:
```json
"filters": {
  "max_age_minutes": 60
}
```

### Summaries are in English instead of Russian

The AI should auto-translate. If not:
1. Check Groq API is working
2. Review `ai_summarizer.py` prompts
3. Report issue on GitHub

### High memory usage

1. Restart bot daily (systemd or PM2)
2. Clear cache: `rm ai_cache.sqlite3`
3. Reduce source count
4. Disable alternative sources

## Performance Questions

### How many news can it handle?

Tested with:
- ✅ 15+ sources
- ✅ 100+ news items per cycle
- ✅ 10-minute intervals
- ✅ Running 24/7

Should handle most use cases.

### Can I run multiple bots on one server?

Yes! Just:
1. Use different directories
2. Different config files
3. Different bot tokens
4. Different ports (if web interface added)

### How to optimize for speed?

1. **Reduce sources**: Keep only important ones
2. **Increase intervals**: 15-30 minutes instead of 10
3. **Disable alternative sources**: Reddit, HN, GitHub
4. **Reduce AI checks**: Lower `max_freshness_checks`
5. **Use caching**: Keep `cache_enabled: true`

## Contribution Questions

### How can I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code contributions
- Documentation improvements
- Bug reports
- Feature suggestions
- Translations

### I found a bug, what should I do?

1. Check if it's already reported in [Issues](https://github.com/yourusername/fap-news/issues)
2. If not, create a new issue with:
   - Clear description
   - Steps to reproduce
   - Error logs
   - Environment details

### Can I add my own news source?

Yes! Either:
1. Use admin panel to add RSS source
2. Submit PR with new source
3. Create HTML parser for non-RSS sources

## Legal Questions

### What license is it under?

MIT License - very permissive:
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ No warranty provided

### Can I use it for commercial purposes?

Yes! MIT license allows commercial use.

### Do I need to credit the project?

Not required, but appreciated! Link back to the repo.

### Can I sell this bot?

Yes, MIT license allows it. But please:
- Keep the open source spirit
- Contribute improvements back
- Don't just rebrand and sell

## Still Have Questions?

- 📖 Check [README.md](README.md)
- 💬 [GitHub Discussions](https://github.com/yourusername/fap-news/discussions)
- 🐛 [Report Issues](https://github.com/yourusername/fap-news/issues)

---

**FAQ last updated: 2025-01-16**
