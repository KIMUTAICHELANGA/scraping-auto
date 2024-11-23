import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse, urljoin
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import hashlib
import schedule
from datetime import datetime

class WebsiteMonitor:
    def __init__(self, start_url):
        self.start_url = start_url
        self.visited_urls = set()
        self.scraped_pages_count = 0
        self.MAX_SCRAPED_PAGES = 1000
        self.PDF_FOLDER = 'pdf_files'
        self.JSON_FILE = 'scraped_data.json'
        self.CHECKSUM_FILE = 'page_checksums.json'
        self.UPDATE_LOG = 'update_log.txt'
        
        # Create necessary folders
        os.makedirs(self.PDF_FOLDER, exist_ok=True)
        
        # Load existing checksums
        self.page_checksums = self.load_checksums()
        
    def load_checksums(self):
        try:
            with open(self.CHECKSUM_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_checksums(self):
        with open(self.CHECKSUM_FILE, 'w') as f:
            json.dump(self.page_checksums, f, indent=4)
    
    def calculate_page_checksum(self, content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def log_update(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.UPDATE_LOG, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def setup_selenium(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options)
    
    def extract_page_data(self, url, depth, driver, max_depth=4):
        if url in self.visited_urls or depth > max_depth or self.scraped_pages_count >= self.MAX_SCRAPED_PAGES:
            return None
        
        self.visited_urls.add(url)
        self.scraped_pages_count += 1
        print(f"Checking URL: {url} (Depth: {depth})")
        
        try:
            driver.get(url)
            
            # Handle dynamic content
            scroll_attempts = 5
            last_height = driver.execute_script("return document.body.scrollHeight")
            while scroll_attempts > 0:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts -= 1
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for tag in soup.find_all(['img', 'link', 'style', 'script']):
                tag.decompose()
            
            page_text = soup.get_text(separator=" ", strip=True)
            current_checksum = self.calculate_page_checksum(page_text)
            
            # Check if page has changed
            if url in self.page_checksums:
                if current_checksum != self.page_checksums[url]:
                    self.log_update(f"Content changed: {url}")
            
            self.page_checksums[url] = current_checksum
            
            links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
            pdf_links = [link for link in links if link.lower().endswith('.pdf')]
            
            page_data = {
                "url": url,
                "depth": depth,
                "content": page_text,
                "links": links,
                "children": [],
                "pdf_links": [],
                "last_updated": datetime.now().isoformat()
            }
            
            # Handle PDFs
            for pdf_link in pdf_links:
                if self.download_pdf(pdf_link):
                    page_data["pdf_links"].append(pdf_link)
            
            # Recursive crawling
            for link in links:
                if urlparse(link).netloc == urlparse(url).netloc and link not in self.visited_urls:
                    child_data = self.extract_page_data(link, depth + 1, driver, max_depth)
                    if child_data:
                        page_data["children"].append(child_data)
            
            return page_data
            
        except Exception as e:
            self.log_update(f"Error scraping {url}: {e}")
            return None
    
    def download_pdf(self, pdf_url):
        pdf_name = os.path.basename(urlparse(pdf_url).path)
        pdf_path = os.path.join(self.PDF_FOLDER, pdf_name)
        try:
            response = requests.get(pdf_url)
            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            self.log_update(f"Failed to download {pdf_url}: {e}")
        return False
    
    def save_all_data_to_json(self, all_data):
        with open(self.JSON_FILE, 'w') as f:
            json.dump(all_data, f, indent=4)
        self.save_checksums()
        print(f"All data saved to {self.JSON_FILE}")
    
    def check_for_updates(self):
        print(f"Starting update check at {datetime.now()}")
        self.visited_urls.clear()
        self.scraped_pages_count = 0
        
        driver = self.setup_selenium()
        all_scraped_data = []
        
        page_data = self.extract_page_data(self.start_url, 0, driver)
        if page_data:
            all_scraped_data.append(page_data)
        
        driver.quit()
        self.save_all_data_to_json(all_scraped_data)
        self.log_update("Update check completed")

def run_monitor(start_url, check_interval_hours=24):
    monitor = WebsiteMonitor(start_url)
    
    # Schedule regular checks
    schedule.every(check_interval_hours).hours.do(monitor.check_for_updates)
    
    # Do initial check
    monitor.check_for_updates()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_url = 'https://aphrc.org'
    run_monitor(start_url, check_interval_hours=24) 