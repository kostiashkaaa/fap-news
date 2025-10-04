# Contributing to FAP News

First off, thank you for considering contributing to FAP News! It's people like you that make FAP News such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Run command '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots/Logs**
If applicable, add screenshots or error logs.

**Environment:**
 - OS: [e.g. Windows 10, Ubuntu 22.04]
 - Python Version: [e.g. 3.11]
 - Bot Version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title** and detailed description
- **Use case**: Why would this enhancement be useful?
- **Proposed solution**: How do you envision this working?
- **Alternatives considered**: What other approaches could work?

### Pull Requests

1. **Fork the repository** and create your branch from `main`:
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**:
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes**:
   ```bash
   python bot.py  # Test main functionality
   ```

4. **Commit your changes**:
   ```bash
   git commit -m "Add amazing feature"
   ```
   
   Follow these commit message guidelines:
   - Use present tense ("Add feature" not "Added feature")
   - Use imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Reference issues: "Fix #123: Description"

5. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request** with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to related issues
   - Screenshots (if applicable)

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- Virtual environment tool

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/fap-news.git
cd fap-news

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config.example.json config.json
# Edit config.json with your test credentials

# Run tests
python bot.py  # Should start without errors
```

## Code Style Guidelines

### Python Style

We follow [PEP 8](https://pep8.org/) with some relaxations:

- Line length: 100-120 characters (soft limit)
- Use type hints where appropriate
- Add docstrings for functions and classes

**Example:**

```python
async def process_news_item(item: NewsItem, config: Dict[str, Any]) -> bool:
    """
    Process a single news item with AI analysis.
    
    Args:
        item: The news item to process
        config: Configuration dictionary
        
    Returns:
        True if successfully processed, False otherwise
    """
    try:
        # Implementation
        return True
    except Exception as e:
        logger.error(f"Failed to process item: {e}")
        return False
```

### File Organization

- Keep related functionality together
- Separate concerns (parsing, posting, AI, etc.)
- Use clear, descriptive names

### Logging

Use the built-in logging module:

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed information for debugging")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

## Project Structure

```
fap-news/
├── bot.py                    # Main entry point
├── parser.py                 # News parsing logic
├── poster.py                 # Telegram posting
├── ai_summarizer.py          # AI integration
├── db.py                     # Database operations
└── config.json              # Configuration
```

## Areas Where We Need Help

### High Priority

- 🐛 Bug fixes and stability improvements
- 📖 Documentation improvements
- 🌍 Internationalization (support for more languages)
- ✅ Unit tests and integration tests

### Medium Priority

- 🔌 New news source integrations
- 🎨 Improved message formatting
- ⚡ Performance optimizations
- 🤖 Enhanced AI prompts

### Low Priority

- 📊 Analytics and statistics
- 🎯 Advanced filtering options
- 🔧 Additional admin features

## Testing

Before submitting a PR:

1. **Manual Testing**:
   - Test with different configurations
   - Verify error handling
   - Check logs for warnings/errors

2. **Integration Testing**:
   - Run the bot for 30+ minutes
   - Verify news collection works
   - Check posting to Telegram

3. **Edge Cases**:
   - Empty responses
   - Network failures
   - Invalid configurations

## Documentation

When adding features:

- Update README.md if user-facing
- Add docstrings to new functions
- Update configuration examples
- Add comments for complex logic

## Release Process

(For maintainers)

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create release tag: `v1.0.0`
4. Publish release notes

## Getting Help

- 💬 [GitHub Discussions](https://github.com/yourusername/fap-news/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/yourusername/fap-news/issues) - Report bugs
- 📧 Create an issue for general questions

## Recognition

Contributors will be:
- Listed in release notes
- Mentioned in the README
- Given credit in commit messages

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to FAP News! 🎉
