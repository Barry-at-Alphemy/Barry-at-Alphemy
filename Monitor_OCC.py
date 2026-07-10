import os
import requests
from bs4 import BeautifulSoup
import hashlib

# Configuration
URL = "https://www.occ.gov/news-events/newsroom/?q=&nr=NewsRelease,Bulletin,Speech,AdvisoryLetter&topic=82&dte=0"
HASH_FILE = "last_hash.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(telegram_url, json=payload)
    else:
        print("Telegram credentials missing.")

def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Target the main body/content area. If specific structure changes, 
    # fallback to the body text to ensure we don't crash.
    main_content = soup.find('main') or soup.find('body')
    if not main_content:
        print("Could not parse page body.")
        return
        
    current_text = main_content.get_text(strip=True)
    current_hash = hashlib.md5(current_text.encode('utf-8')).hexdigest()

    # Read previous hash if it exists
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as f:
            old_hash = f.read().strip()
    else:
        old_hash = None

    # Compare hashes
    if current_hash != old_hash:
        print("Change detected!")
        # Save the new hash
        with open(HASH_FILE, 'w') as f:
            f.write(current_hash)
            
        # ONLY send Telegram alert and trigger Git commit if this isn't the first run
        if old_hash is not None:
            message = f"🔔 *OCC Newsroom Update Detected!*\n\nThe tracked page has updated text or new entries.\n\n[View Page]({URL})"
            send_telegram_alert(message)
        else:
            print("First run initialized. Baseline hash saved.")
    else:
        print("No changes detected today.")

if __name__ == "__main__":
    main()