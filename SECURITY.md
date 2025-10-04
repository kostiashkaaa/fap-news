# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of FAP News seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us responsibly.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via:

1. **GitHub Security Advisories** (Preferred)
   - Go to the Security tab
   - Click "Report a vulnerability"
   - Fill out the form with details

2. **Email** (Alternative)
   - Email: Create a GitHub issue labeled "Security" (keep details minimal)
   - We will respond within 48 hours

### What to Include

When reporting a vulnerability, please include:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Updates**: Regular updates on our progress
- **Resolution**: We aim to resolve critical issues within 7 days
- **Disclosure**: We will coordinate with you on public disclosure

## Security Best Practices

When using FAP News:

### Protect Your Credentials

1. **Never commit** your `config.json` or `.env` files
2. **Use environment variables** for sensitive data
3. **Rotate tokens** regularly
4. **Limit bot permissions** to only what's needed

### Secure Configuration

```json
{
  "telegram": {
    "token": "USE_ENV_VARIABLE",  // Don't hardcode
    "channel_id": "@your_channel"
  }
}
```

### Environment Variables

```bash
# Use .env file (never commit this!)
TELEGRAM_BOT_TOKEN=your_token
GROQ_API_KEY=your_key
```

### Server Security

- Run bot in isolated environment (Docker/VM)
- Use firewall rules to limit network access
- Keep Python and dependencies updated
- Monitor logs for suspicious activity

### Database Security

- The SQLite database is local and doesn't contain sensitive data
- Keep backups encrypted if storing in cloud
- Set appropriate file permissions: `chmod 600 *.sqlite3`

### API Key Security

- Use different API keys for development and production
- Revoke keys immediately if compromised
- Monitor API usage for anomalies
- Set rate limits in configuration

## Known Security Considerations

1. **API Keys in Configuration**: Use environment variables instead of hardcoding
2. **SQLite Database**: No built-in encryption (encrypt filesystem if needed)
3. **Network Requests**: Bot makes HTTP requests to news sources (trust only reputable sources)
4. **AI API**: Data is sent to Groq API for processing (review their privacy policy)

## Updates and Patches

- Security updates are released as soon as possible
- Subscribe to GitHub releases for notifications
- Check CHANGELOG.md for security fixes

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who help improve FAP News security.

---

Last updated: 2025-01-16
