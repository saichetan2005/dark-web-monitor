import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import logging
from time import sleep
from datetime import datetime
from database import init_db  
from config import *


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper.log'
)
logger = logging.getLogger(__name__)

def check_company_leaks(email):
    """Check if email belongs to monitored domains"""
    if not email or '@' not in email:
        return False
    domain = email.split('@')[-1].lower()
    return any(monitored.lower() in domain for monitored in COMPANY_DOMAINS)

def scrape_paste_content(paste_url, cursor, conn):
    try:
        raw_url = paste_url.replace('pastebin.com', 'pastebin.com/raw')
        logger.info(f"Scraping: {raw_url}")
        
        response = requests.get(
            raw_url,
            timeout=10,
            proxies={'http': TOR_PROXY, 'https': TOR_PROXY} if TOR_PROXY else None
        )
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {raw_url} (Status: {response.status_code})")
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
        logger.error(f"Error scraping {paste_url}: {str(e)}")
        conn.rollback()

def scrape_pastebin():
    conn, cursor = init_db()
    try:
        response = requests.get(
            "https://pastebin.com/archive",
            proxies={'http': TOR_PROXY, 'https': TOR_PROXY} if TOR_PROXY else None,
            timeout=10
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.select('td a[href^="/"]:not([href^="/archive"])')[:3]:  
            paste_url = f"https://pastebin.com{link['href']}"
            cursor.execute(
                "INSERT INTO leaks (source, data) VALUES (?, ?)",
                ("Pastebin URL", paste_url)
            )
            conn.commit()
            scrape_paste_content(paste_url, cursor, conn)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        conn.close()
        logger.info("Scraping completed")

if __name__ == "__main__":
    scrape_pastebin()
