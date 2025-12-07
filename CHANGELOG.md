# Changelog

All notable changes to FAP News will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-07

### Added
- **Google News RSS integration** - Collect news by topics and search queries
- **Telegram Channels parser** - Parse public Telegram channels via web interface
- **Centralized configuration module** (`config.py`) with typed dataclasses
- **Database retry logic** with tenacity for better reliability
- **Database migrations** support with schema versioning
- **Bot statistics tracking** with uptime and counters
- **Admin panel status command** - Health check for all components
- **AI cache cleanup** functionality
- **Source priority configuration** - Configure high/medium/low priority sources
- **Queue size limits** - Prevent memory issues with bounded queue

### Changed
- Refactored `bot.py` - Replaced global variables with `NewsBot` class
- Refactored `admin_bot.py` - Added async file operations with aiofiles
- Improved error handling - Replaced bare `except` with specific exceptions
- Updated `parser.py` - Better logging and docstrings
- Enhanced `db.py` - Added WAL mode for better concurrency

### Fixed
- Database concurrency issues with retry logic
- Memory leaks from unbounded queue
- Blocking I/O operations in async code

### Removed
- Deprecated `post_single_item` function
- Hardcoded source priorities (now in config)

## [1.0.0] - 2024-12-01

### Added
- Initial release
- RSS feed parsing
- AI summarization with Groq
- Smart deduplication
- Urgent news detection
- Admin bot for source management
- Docker support
