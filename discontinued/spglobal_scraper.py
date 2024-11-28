import time
import logging
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logging.basicConfig(
    filename='esg_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class ESGScraper:
    def __init__(self):
        self.URL = "https://www.spglobal.com/esg/scores/"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        # options.page_load_strategy = 'eager'
        
        self.driver = webdriver.Chrome(options=options)
        
    def initialize_site(self):
        self.driver.get(self.URL)
        time.sleep(1)
        
        try:
            cookies_button = WebDriverWait(self.driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
            )
            cookies_button.click()
        except TimeoutException:
            pass
    
    def get_search_bar(self):
        search_bar_xpaths = [
            '//input[@placeholder="Search for a company\'s ESG Score*"]',
            '//input[@class="banner-search__input"]'
        ]
        
        for xpath in search_bar_xpaths:
            try:
                return WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
            except TimeoutException:
                continue
                
        raise TimeoutException("Could not find search bar")
    
    def search_company(self, company_name):
        search_bar = self.get_search_bar()
        search_bar.clear()
        search_bar.send_keys(company_name + Keys.RETURN)
        time.sleep(1)
        
        try:
            WebDriverWait(self.driver, 5).until(
                EC.staleness_of(self.driver.find_element(By.XPATH, '//*[@class="scoreModule__score"]'))
            )
        except:
            pass
    
        time.sleep(2)
    
    def get_score(self):
        try:
            score = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="scoreModule__score"]'))
            )
            
            if score and score.is_displayed():
                return score.text
            return None
        except:
            return None
    
    def close(self):
        if self.driver:
            self.driver.quit()

def process_companies(companies):
    scraper = ESGScraper()
    results = []
    
    try:
        scraper.initialize_site()
        
        for company in companies:
            scraper.search_company(company)
            score = scraper.get_score()
            results.append({
                'company': company,
                'esg_score': score
            })
            print(f"Found score for {company}: {score}")  
            time.sleep(2)  
            
    finally:
        scraper.close()
    
    return results

if __name__ == "__main__":
    companies = ["Microsoft Corporation"]
    results = process_companies(companies)
    
    print("\nFinal Results:")
    for result in results:
        print(f"{result['company']}: {result['esg_score']}")
#"Apple Inc.", e