import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse, urljoin
import time
import hashlib
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)

class WebsiteMonitor:
    def __init__(self, start_url, output_dir='data'):
        self.start_url = start_url
        self.visited_urls = set()
        self.domain = urlparse(start_url).netloc
        
        # Setup directories
        self.output_dir = output_dir
        self.pdf_dir = os.path.join(output_dir, 'pdf_files')
        self.data_dir = os.path.join(output_dir, 'scraped_data')
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.checksum_file = os.path.join(self.data_dir, 'checksums.json')
        self.content_file = os.path.join(self.data_dir, 'content.json')
        
        # Load existing data
        self.checksums = self._load_json(self.checksum_file, {})
        self.content = self._load_json(self.content_file, {})
        
        self.logger = logging.getLogger(__name__)

    def _load_json(self, filepath, default):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return default

    def _save_json(self, data, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _get_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    def _calculate_checksum(self, content):
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _has_content_changed(self, url, new_checksum):
        return url not in self.checksums or self.checksums[url] != new_checksum

    def _extract_text(self, soup):
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer']):
            element.decompose()
        
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        return ' '.join(text.split())

    def _process_page(self, driver, url):
        try:
            driver.get(url)
            time.sleep(2)  # Wait for dynamic content
            
            # Scroll to load dynamic content
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            text_content = self._extract_text(soup)
            new_checksum = self._calculate_checksum(text_content)
            
            # Check for changes
            if self._has_content_changed(url, new_checksum):
                self.logger.info(f"Content changed: {url}")
                self.checksums[url] = new_checksum
                self.content[url] = {
                    'content': text_content,
                    'last_updated': datetime.now().isoformat(),
                    'title': soup.title.string if soup.title else url
                }
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error processing {url}: {e}")
            return False

    def _get_links(self, driver):
        elements = driver.find_elements(By.TAG_NAME, "a")
        links = []
        for element in elements:
            try:
                href = element.get_attribute('href')
                if href and urlparse(href).netloc == self.domain:
                    links.append(href)
            except:
                continue
        return list(set(links))

    def check_for_updates(self):
        self.logger.info("Starting website check...")
        driver = self._get_driver()
        changes_detected = False
        self.visited_urls.clear()
        
        try:
            queue = [self.start_url]
            while queue:
                url = queue.pop(0)
                if url in self.visited_urls:
                    continue
                    
                self.visited_urls.add(url)
                self.logger.info(f"Checking: {url}")
                
                if self._process_page(driver, url):
                    changes_detected = True
                
                # Add new links to queue
                links = self._get_links(driver)
                queue.extend([link for link in links if link not in self.visited_urls])
                
            if changes_detected:
                self._save_json(self.checksums, self.checksum_file)
                self._save_json(self.content, self.content_file)
                
            self.logger.info("Website check completed")
            return changes_detected
            
        except Exception as e:
            self.logger.error(f"Error during website check: {e}")
            return False
        finally:
            driver.quit()

    def get_changed_content(self):
        """Returns the latest content that has changed"""
        return self.content