import os
import sqlite3
import time
import difflib
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from colorama import init, Fore, Style
from prettytable import PrettyTable
import threading
import sys

# Initialize colorama
init(autoreset=True)

# Constants
BBC_URL = "https://www.bbc.com"
DB_NAME = "headlines.db"

class Spinner:
    """A simple loading spinner for the CLI"""
    def __init__(self, message=""):
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.message = message
        self.stop_spinner = False
        self.thread = None

    def spin(self):
        """Spin the spinner in a separate thread"""
        i = 0
        while not self.stop_spinner:
            sys.stdout.write(f"\r{self.spinner_chars[i % len(self.spinner_chars)]} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
        sys.stdout.flush()

    def start(self):
        """Start the spinner"""
        self.thread = threading.Thread(target=self.spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, success=True):
        """Stop the spinner with success or error indicator"""
        self.stop_spinner = True
        if self.thread:
            self.thread.join()
        if success:
            print(f"\r{Fore.GREEN}✓{Style.RESET_ALL} {self.message} - Done!")
        else:
            print(f"\r{Fore.RED}✗{Style.RESET_ALL} {self.message} - Failed!")

def print_header():
    """Print the application header"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════╗
    ║         {Fore.WHITE}📰 BBC HEADLINE NOTIFIER{Fore.CYAN}         ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}
    """)

def print_status(message, status_type="info"):
    """Print a status message with colored output"""
    if status_type == "success":
        print(f"{Fore.GREEN}[✓] {message}{Style.RESET_ALL}")
    elif status_type == "error":
        print(f"{Fore.RED}[✗] {message}{Style.RESET_ALL}")
    elif status_type == "warning":
        print(f"{Fore.YELLOW}[!] {message}{Style.RESET_ALL}")
    else:
        print(f"[•] {message}")

def setup_database():
    """Set up the SQLite database"""
    spinner = Spinner("Initializing database...")
    spinner.start()
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS headlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        spinner.stop(True)
        return conn
    except Exception as e:
        spinner.stop(False)
        print_status(f"Error setting up database: {e}", "error")
        return None

def get_telegram_credentials():
    """Load Telegram credentials from .env file
    
    Returns:
        tuple: (token, chat_ids) where chat_ids is a list of chat IDs
    """
    load_dotenv()
    token = os.getenv('TELEGRAM_TOKEN')
    chat_ids = os.getenv('TELEGRAM_CHAT_IDS', '').split(',')
    
    # Clean up chat IDs (remove whitespace and empty strings)
    chat_ids = [cid.strip() for cid in chat_ids if cid.strip()]
    
    if not token or not chat_ids:
        print_status("Telegram credentials not properly configured in .env file", "error")
        return None, []
    return token, chat_ids

def send_telegram_notification(message):
    """Send a notification to all registered Telegram chats
    
    Args:
        message (str): The message to send
        
    Returns:
        tuple: (success_count, total_attempts) number of successful sends and total attempts
    """
    token, chat_ids = get_telegram_credentials()
    if not token or not chat_ids:
        print_status("No token or chat IDs found. Cannot send notifications.", "error")
        return 0, 0
    
    success_count = 0
    total_attempts = len(chat_ids)
    
    print_status(f"Preparing to send message to {total_attempts} recipients...")
    
    for chat_id in chat_ids:
        try:
            print_status(f"Sending to chat ID: {chat_id}...")
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            print_status(f"Sending request to Telegram API...")
            response = requests.post(url, json=payload, timeout=15)
            
            print_status(f"Response status: {response.status_code}")
            if response.status_code == 200:
                success_count += 1
                print_status(f"Successfully sent to chat ID: {chat_id}", "success")
            else:
                print_status(f"Failed to send to chat ID {chat_id}. Status: {response.status_code}, Response: {response.text}", "error")
                
        except Exception as e:
            print_status(f"Error sending to chat ID {chat_id}: {str(e)[:100]}...", "error")
    
    return success_count, total_attempts

def fetch_headlines():
    """Fetch the latest headlines from BBC News"""
    spinner = Spinner(f"{Fore.CYAN}Fetching latest headlines from BBC News...")
    spinner.start()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(BBC_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        
        # Try multiple selectors to find headlines
        selectors = [
            'a[data-testid="internal-link"]',  # Main headlines
            'a.bbc-1f5kfds',  # Alternative selector 1
            'a.gs-c-promo-heading',  # Alternative selector 2
            'a.ssrcss-1mrs5ns-PromoLink'  # Alternative selector 3
        ]
        
        for selector in selectors:
            if headlines:  # If we already found headlines, no need to try other selectors
                break
                
            for a in soup.select(selector):
                # Get the text from either the link itself or its child elements
                title = a.get_text(' ', strip=True)
                
                # Skip if title is too short or doesn't look like a proper headline
                if not title or len(title) < 10 or len(title) > 150:
                    continue
                    
                # Get the URL
                url = a.get('href', '')
                if not url:
                    continue
                    
                # Make relative URLs absolute
                if url.startswith('/'):
                    url = f"{BBC_URL}{url}"
                elif not url.startswith(('http://', 'https://')):
                    continue  # Skip invalid URLs
                
                # Skip duplicate URLs
                if any(h['url'] == url for h in headlines):
                    continue
                
                headlines.append({
                    'title': title,
                    'url': url
                })
                
                # Limit to top 20 headlines to avoid too many results
                if len(headlines) >= 20:
                    break
        
        spinner.stop(True)
        return headlines
    except Exception as e:
        spinner.stop(False)
        print_status(f"Error fetching headlines: {e}", "error")
        return []

def display_headlines(headlines, title="Latest Headlines"):
    """Display headlines in a pretty table"""
    if not headlines:
        print_status("No headlines to display.", "warning")
        return
    
    table = PrettyTable()
    # Set field names with colors
    table.field_names = [
        f"{Fore.CYAN}#{Style.RESET_ALL}",
        f"{Fore.CYAN}Headline{Style.RESET_ALL}",
        f"{Fore.CYAN}Link{Style.RESET_ALL}"
    ]
    
    # Configure alignment
    table.align["Headline"] = "l"
    table.max_width = 120  # Limit table width
    
    # Add rows with proper formatting
    for idx, item in enumerate(headlines[:15], 1):  # Show top 15
        # Truncate long titles for better display
        title = item['title']
        if len(title) > 60:
            title = title[:57] + '...'
            
        # Truncate URL for display
        display_url = item['url']
        if len(display_url) > 30:
            display_url = '...' + display_url[-27:]
            
        table.add_row([
            f"{Fore.YELLOW}{idx}{Style.RESET_ALL}",
            title,
            f"{Fore.BLUE}{display_url}{Style.RESET_ALL}"
        ])
    
    # Print the table with a nice border
    print(f"\n{Fore.CYAN}┏━━━━ {title} ━━━━┓{Style.RESET_ALL}")
    print(table)
    print(f"{Fore.CYAN}┗━━━━ {len(headlines)} headlines found ━━━━┛{Style.RESET_ALL}\n")
    
    # Print full URLs for reference
    if len(headlines) > 0:
        print(f"{Fore.YELLOW}Full article links:{Style.RESET_ALL}")
        for idx, item in enumerate(headlines[:5], 1):
            print(f"{idx}. {item['url']}")
        if len(headlines) > 5:
            print(f"... and {len(headlines) - 5} more")
        print()  # Add an extra newline

def save_headlines(conn, headlines):
    """Save new headlines to the database"""
    if not headlines:
        return []
    
    cursor = conn.cursor()
    new_headlines = []
    
    for item in headlines:
        # Check if headline already exists
        cursor.execute(
            'SELECT id FROM headlines WHERE title = ?', 
            (item['title'],)
        )
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO headlines (title, url) VALUES (?, ?)',
                (item['title'], item['url'])
            )
            new_headlines.append(item)
    
    conn.commit()
    return new_headlines

def send_test_notification():
    """Send a test notification to verify Telegram setup"""
    test_message = "📡 <b>BBC Headline Notifier - Connection Successful</b>\n\n" \
                 "Your notification service is now active and ready to deliver the latest BBC headlines.\n" \
                 "Next update: When new headlines are published.\n\n" \
                 "<i>This is an automated message. No action is required.</i>"
    
    success_count, total_attempts = send_telegram_notification(test_message)
    if success_count > 0:
        print_status(f"✅ Test notification sent successfully to {success_count} out of {total_attempts} recipients!", "success")
        print_status("Check your Telegram to confirm receipt.", "success")
    else:
        print_status("❌ Failed to send test notification. Please check your Telegram bot token and chat IDs.", "error")

def is_first_run():
    """Check if this is the first run by looking at the database"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM headlines")
        count = cursor.fetchone()[0]
        return count == 0
    except:
        return True
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function to run the scraper"""
    print_header()
    
    # Check for Telegram credentials
    token, chat_ids = get_telegram_credentials()
    if not token or not chat_ids:
        print_status("Telegram credentials not properly configured. Notifications will be disabled.", "warning")
    else:
        print_status(f"Found Telegram token and {len(chat_ids)} chat ID(s)", "success")
        
        # Send test notification on first run
        if is_first_run():
            print_status("This appears to be the first run. Sending test notification...", "warning")
            send_test_notification()
    
    # Initialize database
    conn = setup_database()
    if not conn:
        return
    
    try:
        # Fetch and process headlines
        headlines = fetch_headlines()
        if not headlines:
            print_status("No headlines found. Please check your internet connection.", "error")
            return
        
        # Display headlines
        display_headlines(headlines)
        
        # Save new headlines
        new_headlines = save_headlines(conn, headlines)
        
        # Send notifications for new headlines
        if new_headlines:
            if token and chat_ids:
                print_status(f"\n{Fore.CYAN}📡 Sending {len(new_headlines)} new headlines to {len(chat_ids)} recipients...{Style.RESET_ALL}")
                message = "<b>📰 Latest BBC Headlines</b>\n\n"
                
                for idx, item in enumerate(new_headlines[:5], 1):  # Limit to 5 to avoid message limits
                    title = item['title']
                    # Truncate long titles to prevent hitting Telegram's message length limit
                    if len(title) > 80:
                        title = title[:77] + '...'
                    message += f"{idx}. <b>{title}</b>\n<a href='{item['url']}'>Read more →</a>\n\n"
                
                success_count, total_attempts = send_telegram_notification(message)
                if success_count > 0:
                    print_status(f"✅ Successfully sent to {success_count} out of {total_attempts} recipients", "success")
                    print_status("Check your Telegram app for the updates!", "success")
                else:
                    print_status("❌ Failed to send to any recipients. Check your internet connection and Telegram bot settings.", "error")
            else:
                print_status("⚠️  Telegram notifications are disabled due to missing credentials", "warning")
        
        print_status("Scraping complete!", "success")
        
    except KeyboardInterrupt:
        print("\n" + "="*50)
        print_status("Operation cancelled by user", "warning")
    except Exception as e:
        print_status(f"An error occurred: {e}", "error")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
