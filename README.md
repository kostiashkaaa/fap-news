# 🗞️ FAP News — AI-Powered Telegram News Aggregator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

An intelligent Telegram bot that automatically collects, translates, summarizes, and publishes news from multiple international sources using AI-powered analysis.

## ✨ Features

### 🤖 **AI-Powered Intelligence**
- **Smart Summarization**: Uses Groq AI (LLaMA 3.1) to create concise, informative summaries
- **Urgency Detection**: Automatically identifies breaking news for immediate posting
- **Freshness Analysis**: Filters old news to keep your channel current
- **Importance Scoring**: Adapts summary length based on news significance
- **Smart Deduplication**: Semantic analysis to avoid duplicate stories

### 📰 **Multi-Source News Aggregation**
- RSS feed support from 15+ major news sources (BBC, CNN, Reuters, NYT, Guardian, etc.)
- Alternative sources: Reddit, Hacker News, GitHub Trending
- Support for both Russian and international news
- Customizable source priorities

### 🎯 **Advanced Filtering**
- Keyword-based filtering (include/exclude lists)
- Age-based filtering (configurable time window)
- Smart content analysis to avoid irrelevant news

### 🚀 **Automation**
- Scheduled news collection (configurable intervals)
- Queue-based posting with smart delays
- Automatic translation to Russian
- Built-in caching to reduce API costs

### 🛠️ **Admin Panel**
- Telegram-based admin interface
- Dynamic source management
- Real-time statistics
- Easy configuration

## 📋 Prerequisites

- Python 3.11 or higher
- Telegram Bot Token ([get from @BotFather](https://t.me/botfather))
- Groq API Key (optional, [get free key](https://console.groq.com/))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/fap-news.git
cd fap-news
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Bot

#### Option A: Using Environment Variables

Create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id_here
GROQ_API_KEY=your_groq_api_key_here  # Optional
```

#### Option B: Using config.json

Copy the example configuration:

```bash
cp config.example.json config.json
```

Edit `config.json` and add your credentials:

```json
{
  "telegram": {
    "token": "YOUR_BOT_TOKEN",
    "channel_id": "@your_channel"
  },
  "ai_summarization": {
    "enabled": true,
    "api_key": "YOUR_GROQ_API_KEY"
  },
  "admin": {
    "allowed_user_ids": [YOUR_USER_ID]
  }
}
```

**To get your Telegram User ID:**
- Message [@userinfobot](https://t.me/userinfobot) on Telegram

### 5. Run the Bot

```bash
# Main bot (news collection and posting)
python bot.py

# Admin panel (in separate terminal)
python admin_bot.py
```

## 📖 Detailed Documentation

### Configuration Options

#### Telegram Settings
```json
"telegram": {
  "token": "YOUR_BOT_TOKEN",
  "channel_id": "@your_channel_or_chat_id"
}
```

#### News Sources
You can add RSS feeds or HTML sources:

```json
"sources": [
  {
    "name": "Source Name",
    "tag": "#sourcetag",
    "rss": "https://example.com/rss",
    "priority": 1  // 1=highest, 3=lowest
  }
]
```

#### Filters
```json
"filters": {
  "include_keywords": ["Ukraine", "Russia", "USA"],  // Only these topics
  "exclude_keywords": ["sports", "celebrity"],        // Skip these
  "max_age_hours": 24,                                // Ignore old news
  "max_age_minutes": 120                              // Alternative time limit
}
```

#### AI Summarization
```json
"ai_summarization": {
  "enabled": true,
  "provider": "groq",
  "api_key": "YOUR_API_KEY",
  "model": "llama-3.1-8b-instant",
  "max_summary_length": 500,
  "cache_enabled": true  // Save API costs
}
```

#### Posting Schedule
```json
"scheduler": {
  "interval_minutes": 10  // Check for news every 10 minutes
},
"posting": {
  "min_delay_minutes": 1,  // Minimum time between posts
  "max_delay_minutes": 4   // Maximum time between posts
}
```

### Admin Commands

Start the admin bot and send `/admin` or `/start` to access:

- 📰 **Manage Sources**: Add/remove news sources
- ⚙️ **Filter Settings**: View current filters
- 📊 **Statistics**: See posting stats

### Project Structure

```
fap-news/
├── bot.py                        # Main bot (news collection & posting)
├── admin_bot.py                  # Admin panel bot
├── parser.py                     # RSS/HTML parsing
├── poster.py                     # Message formatting & Telegram posting
├── ai_summarizer.py              # AI-powered summarization
├── smart_deduplicator.py         # Duplicate detection
├── news_importance_analyzer.py   # News importance scoring
├── alternative_sources.py        # Reddit, HN, GitHub integration
├── ai_cache.py                   # AI response caching
├── db.py                         # SQLite database
├── config.json                   # Main configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🔧 Advanced Features

### Smart Deduplication

The bot uses semantic analysis to detect duplicate news:

```json
"deduplication": {
  "enabled": true,
  "similarity_threshold": 0.7,  // 0-1, higher = stricter
  "title_weight": 0.6,           // Importance of title similarity
  "content_weight": 0.4          // Importance of content similarity
}
```

### Alternative News Sources

Enable additional sources beyond RSS:

```json
"alternative_sources": {
  "reddit": {
    "enabled": true,
    "subreddits": ["worldnews", "news", "politics"]
  },
  "newsapi": {
    "enabled": false,
    "api_key": "YOUR_NEWSAPI_KEY"
  }
}
```

### AI Caching

Reduces API costs by caching AI responses:

```json
"ai_summarization": {
  "cache_enabled": true,
  "cache_ttl_hours": 24  // Cache lifetime
}
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 🐛 Troubleshooting

### Bot doesn't post messages
- Verify bot token in `config.json` or `.env`
- Check that bot is admin in the target channel
- Review logs in console for errors

### AI summarization not working
- Verify Groq API key is correct
- Check [Groq status page](https://status.groq.com/)
- Review rate limits in configuration

### Missing dependencies
```bash
pip install -r requirements.txt --upgrade
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [Groq](https://groq.com/) - Fast AI inference
- [feedparser](https://github.com/kurtmckee/feedparser) - RSS parsing
- All open-source contributors

## 📧 Contact

- Create an [Issue](https://github.com/yourusername/fap-news/issues) for bugs or features
- [Discussions](https://github.com/yourusername/fap-news/discussions) for questions

## ⭐ Support

If you find this project useful, please consider:
- Giving it a ⭐ on GitHub
- Sharing it with others
- Contributing improvements

---

**Made with ❤️ for the open source community**