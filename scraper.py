import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import logging
from time import sleep
from datetime import datetime
from config import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper.log'
)
logger = logging.getLogger(__name__)

def scrape_paste_content(paste_url, cursor, conn):
    try:
        raw_url = paste_url.replace('pastebin.com', 'pastebin.com/raw')
        logger.info(f"Scraping: {raw_url}")
        
        response = requests.get(
            raw_url, 
            timeout=10,
            proxies={'http': TOR_PROXY, 'https': TOR_PROXY} if TOR_PROXY else None
        )
        
        if "has been blocked" in response.text:
            logger.error("PASTEBIN BLOCKED - Use Tor or proxies")
            return
            
        content = response.text
        logger.debug(f"Content sample: {content[:100]}...")
        
        patterns = [
            r'([\w\.\+\-]+@[\w\-]+\.[\w\.\-]+)[\:\|\;\,\s]\s*([^\s]+)', 
            r'(user(name)?|login)[\:\=]\s*([^\s]+)\s+(pass(word)?|pwd)[\:\=]\s*([^\s]+)'  
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                username = match.group(1)
                password = match.group(2) if len(match.groups()) == 2 else match.group(3)
                
                logger.info(f"Found: {username}:{password}")
                cursor.execute(
                    "INSERT INTO leaks (source, data, is_critical) VALUES (?, ?, ?)",
                    (paste_url, f"{username}:{password}", 1 if check_company_leaks(username) else 0)
                )
                conn.commit()
                
        sleep(REQUEST_DELAY)
    except Exception as e:
        logger.error(f"Error: {e}")

def scrape_pastebin():
    conn, cursor = init_db()
    try:
        response = requests.get(
            "https://pastebin.com/archive",
            proxies={'http': TOR_PROXY, 'https': TOR_PROXY} if TOR_PROXY else None
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.select('td a[href^="/"]:not([href^="/archive"])')[:5]:
            paste_url = f"https://pastebin.com{link['href']}"
            scrape_paste_content(paste_url, cursor, conn)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    scrape_pastebin()
