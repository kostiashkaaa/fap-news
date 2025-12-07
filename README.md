# 📰 FAP News Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg?logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![AI](https://img.shields.io/badge/AI-Groq%20LLaMA-purple.svg)

**Intelligent Telegram News Aggregator with AI-Powered Summarization**

[🇷🇺 Russian Documentation](README_RU.md) | [📖 Quick Start](QUICKSTART.md) | [🚀 Deployment](DEPLOYMENT.md)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📡 **Multi-Source Collection** | RSS feeds, Google News, Telegram channels |
| 🤖 **AI Summarization** | Groq LLaMA-powered smart summaries |
| 🚨 **Urgent News Detection** | Instant publishing of breaking news |
| 🧹 **Smart Deduplication** | Semantic similarity filtering |
| ⚡ **Priority-Based Publishing** | Configurable source priorities |
| 📊 **Admin Panel** | Telegram bot for source management |
| 💾 **Intelligent Caching** | Reduces API costs significantly |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FAP News Bot                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │   RSS   │  │ Google  │  │Telegram │  │  Alternative    │ │
│  │  Feeds  │  │  News   │  │Channels │  │   Sources       │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
│       │            │            │                │          │
│       └────────────┴────────────┴────────────────┘          │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │   Parser    │                          │
│                    │  & Filter   │                          │
│                    └──────┬──────┘                          │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │    Smart    │                          │
│                    │Deduplicator │                          │
│                    └──────┬──────┘                          │
│                           │                                 │
│            ┌──────────────┴──────────────┐                  │
│            │                             │                  │
│     ┌──────▼──────┐              ┌───────▼───────┐          │
│     │   Urgency   │              │  Importance   │          │
│     │   Checker   │              │   Analyzer    │          │
│     └──────┬──────┘              └───────┬───────┘          │
│            │                             │                  │
│     ┌──────▼──────┐              ┌───────▼───────┐          │
│     │    Groq     │◄────────────►│   AI Cache    │          │
│     │     API     │              │   (SQLite)    │          │
│     └──────┬──────┘              └───────────────┘          │
│            │                                                │
│     ┌──────▼──────┐                                         │
│     │  Telegram   │                                         │
│     │   Channel   │                                         │
│     └─────────────┘                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Groq API Key (free at [groq.com](https://console.groq.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fap-news.git
cd fap-news

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.example.json config.json
# Edit config.json with your tokens
```

### Configuration

Edit `config.json`:

```json
{
  "telegram": {
    "token": "YOUR_BOT_TOKEN",
    "channel_id": "@your_channel"
  },
  "ai_summarization": {
    "enabled": true,
    "api_key": "YOUR_GROQ_API_KEY"
  }
}
```

### Run

```bash
# Run the main bot
python bot.py

# Or run both bots (main + admin)
python run_all.py
```

---

## 📦 Project Structure

```
fap-news/
├── bot.py                    # Main news bot
├── admin_bot.py              # Admin panel bot
├── parser.py                 # RSS/HTML parsing
├── poster.py                 # Telegram posting
├── db.py                     # Database operations
├── config.py                 # Configuration management
├── ai_summarizer.py          # AI summarization (Groq)
├── ai_cache.py               # AI response caching
├── smart_deduplicator.py     # Semantic deduplication
├── news_importance_analyzer.py # Content importance scoring
├── google_news.py            # Google News RSS collector
├── telegram_channels.py      # Telegram channel parser
├── alternative_sources.py    # Additional news sources
├── config.example.json       # Configuration template
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker support
└── docker-compose.yml        # Docker Compose config
```

---

## 📰 Supported News Sources

### RSS Feeds (16+ configured)
- BBC, Reuters, Fox News, CNN, NYT
- Washington Post, The Guardian, Financial Times
- RT, TASS, RIA Novosti
- Al Jazeera, Deutsche Welle, Euronews
- And many more...

### Google News
- Topic-based feeds (World, Politics, Business)
- Custom search queries (Russia, Ukraine, NATO, etc.)

### Telegram Channels
- BBC Russian, Mash, RIA, TASS
- Easily add more channels

---

## ⚙️ Configuration Options

| Section | Option | Description |
|---------|--------|-------------|
| `telegram` | `token` | Bot API token |
| `telegram` | `channel_id` | Target channel ID |
| `ai_summarization` | `enabled` | Enable/disable AI |
| `ai_summarization` | `api_key` | Groq API key |
| `posting` | `min_delay_minutes` | Min delay between posts |
| `posting` | `max_queue_size` | Maximum queue size |
| `source_priority` | `high_priority` | High priority sources |
| `deduplication` | `similarity_threshold` | Duplicate detection (0-1) |

See [config.example.json](config.example.json) for full options.

---

## 🤖 Admin Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Open admin panel |
| `/admin` | Same as /start |
| **Buttons** | |
| 📰 Sources | Manage news sources |
| ⚙️ Filters | View filter settings |
| 📊 Stats | View statistics |
| 🔍 Status | Bot health check |

---

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## 📊 Performance

- **Collection**: ~300-400 news items per cycle
- **AI Caching**: Reduces API calls by ~70%
- **Deduplication**: Filters ~30-50% duplicates
- **Publishing**: 1-4 minute intervals

---

## 🛠️ Development

```bash
# Run diagnosis
python diagnose.py

# Test posting
python test_send.py

# Force publish one news
python force_post.py
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📞 Support

- 📖 [FAQ](FAQ.md)
- 🐛 [Issues](https://github.com/yourusername/fap-news/issues)
- 💬 [Discussions](https://github.com/yourusername/fap-news/discussions)

---

<div align="center">

**Made with ❤️ for news aggregation**

⭐ Star this repo if you find it useful!

</div>