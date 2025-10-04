# 📰 BBC News Headline Notifier

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional Python automation tool that monitors BBC News headlines and delivers real-time updates directly to your Telegram. Perfect for staying informed without constantly checking the news.

## ✨ Features

- **Real-time Monitoring**: Get instant notifications when new headlines are published
- **Smart Deduplication**: Only receive notifications for genuinely new content
- **Rich Formatting**: Beautifully formatted messages with direct article links
- **Multi-User Support**: Send updates to multiple Telegram chat IDs
- **Persistent Storage**: SQLite database tracks seen headlines between runs
- **Reliable**: Built-in error handling and retry mechanisms

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- A Telegram account
- Basic terminal/command line knowledge

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/evilshxt/bbc-notifier.git
   cd bbc-notifier
   ```

2. **Set up a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Telegram Bot Setup

### 1. Create a New Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and use the `/newbot` command
3. Follow the prompts to name your bot
4. Copy the API token provided by BotFather

### 2. Get Your Chat ID
1. Send a message to your new bot
2. Visit this URL in your browser (replace `YOUR_TOKEN` with your actual bot token):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Look for the `"chat":{"id":123456789}` in the JSON response

### 3. Configure Environment
1. Create a `.env` file in the project root
2. Add your credentials:
   ```env
   TELEGRAM_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_IDS=your_chat_id,another_chat_id  # Separate multiple IDs with commas
   ```
   Example:
   ```env
   TELEGRAM_TOKEN=1234567890:ABCdefGhijKLMnopQRstuvWXyz
   TELEGRAM_CHAT_IDS=5571315124,7999218249
   ```

## 🏃‍♂️ Running the Scraper

### Basic Usage
```bash
python scraper.py
```

### Schedule Regular Updates

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create a new task
3. Set trigger to "Daily" and select your preferred time
4. Action: Start a program
   - Program: `pythonw.exe`
   - Arguments: `"C:\path\to\scraper.py"`
   - Start in: `C:\path\to\project\`

#### Linux/macOS (cron)
```bash
# Edit crontab
crontab -e

# Add this line to run every hour
0 * * * * cd /path/to/project && /usr/bin/python3 scraper.py >> scraper.log 2>&1
```

## 🛠 Project Structure
```
bbc-headline-notifier/
├── scraper.py      # Main script
├── headlines.db    # SQLite database
├── .env            # Environment variables (not in version control)
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## 🔐 Security Best Practices

- **Never commit sensitive data**: Your `.env` file is in `.gitignore` by default
- **Token security**: If your bot token is compromised, revoke it immediately using `/revoke` in @BotFather
- **Environment variables**: Always use environment variables for sensitive data
- **Virtual environment**: Always use a virtual environment to manage dependencies

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- [BBC News](https://www.bbc.com) for the content
- [Python Telegram Bot API](https://python-telegram-bot.org/) for the notification system
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for web scraping
- [python-dotenv](https://github.com/theskumar/python-dotenv) for environment variable management