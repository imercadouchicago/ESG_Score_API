from esg_app.utils.scraper_utils.scraper import WebScraper
from esg_app.utils.scraper_utils.threader import Threader
from esg_app.utils.scraper_utils.msci_utils import (clean_company_name,
                                                    get_flag_color)
import logging
import pandas as pd
from queue import Queue
from tqdm import tqdm
from threading import Lock
from time import sleep
import censusname

# Configure logging
logging.basicConfig(
    filename='parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

URL = "https://www.msci.com/our-solutions/esg-investing/esg-ratings-climate-search-tool"
headername = 'Shortname'
export_path = 'esg_app/api/data/msci_esg_scores.csv'

def msci_scraper(company_data: pd.DataFrame, user_agents: Queue, processed_tickers: set, lock: Lock) -> list[dict]:
    try:
        # Initialize browser
        bot = WebScraper(URL, user_agents)
        sleep(10)
        output = []

        # Accept cookies
        cookies_path = "onetrust-accept-btn-handler"
        cookie_button = bot.accept_cookies(id_name=cookies_path)
        # cookie_button = bot.wait_element_to_load(id_name=cookies_path, button=True)
        # cookie_button.click()

        for index, row in tqdm(company_data.iterrows(),
                                total=len(company_data),
                                desc=f"Processing chunk",
                                position=1,
                                leave=False):
            try:
                with lock:
                    if row[headername] in processed_tickers:
                        logging.info(f"Skipping already processed company: {row[headername]}")
                        continue
                    processed_tickers.add(row[headername])
                logging.debug(f"Processing company: {row[headername]}")  
                
                # Data cleaning
                company_name = row[headername]
                cleaned_name = clean_company_name(company_name)
                
                # Send request to search bar
                bot.driver.get(URL)
                bot.send_request_to_search_bar(cleaned_name, id_name="_esgratingsprofile_keywords")
                
                dropdown = bot.locate_element(class_name="ui-autocomplete")
                results = bot.locate_element_within_element(dropdown, class_name="msci-ac-search-section-title", multiple = True)

                for result in results:
                    result_name = result.get_attribute('data-value')
                    cleaned_result = clean_company_name(result_name)
                    if cleaned_result == cleaned_name:
                        # Try different click methods
                        try:
                                bot.driver.execute_script("arguments[0].click();", result)
                        except:
                            try:
                                result.click()
                            except:
                                parent = bot.locate_element_within_element(result, xpath="..")
                                bot.driver.execute_script("arguments[0].click();", parent)
                        logging.info("Found match in dropdown: %s", cleaned_result)
                        sleep(5)

                        if bot.is_subscription_form_present(id_name="_esgratingsprofile_esg-subscription-form-container"):
                            try:
                                # Generate names using censusname
                                first_name = censusname.generate(nameformat='{given}')
                                last_name = censusname.generate(nameformat='{surname}')
                                job_title = "Analyst"
                                company_name = "ESG Investment Group"
                                email = f"{first_name}.{last_name}@{company_name.replace(' ', '').lower()}.com"
                                
                                bot.fill_field(first_name, id_name="_esgratingsprofile_firstName")
                                bot.fill_field(last_name, id_name="_esgratingsprofile_lastName")
                                bot.fill_field(job_title, id_name="_esgratingsprofile_jobTitle")
                                bot.fill_field(email, id_name="_esgratingsprofile_email")
                                bot.fill_field(company_name, id_name="_esgratingsprofile_company")
                                bot.select_dropdown("ASSET_MANAGERS", id_name="_esgratingsprofile_Clics_Segment")
                                bot.select_dropdown("PORTFOLIO", id_name="_esgratingsprofile_Primary_Area_Of_Interest")
                                bot.select_dropdown("AUSTRALIA", id_name="_esgratingsprofile_country")
                            except Exception as e:
                                logging.warning("Failure to fill our subscription form: %s", e)
                        
                        # Click ESG transparency toggle
                        toggle_path = "esg-transparency-toggle-link"
                        toggle = bot.locate_element(id_name=toggle_path)
                        # toggle = bot.wait_element_to_load(id_name=toggle_path, button = True)
                        toggle.click()
                        logging.info("Clicked ESG transparency toggle")
                        sleep(5)

                        # Locate ESG Rating
                        rating_map = {
                                    "esg-rating-circle-aaa": "AAA",
                                    "esg-rating-circle-aa": "AA",
                                    "esg-rating-circle-a": "A",
                                    "esg-rating-circle-bbb": "BBB",
                                    "esg-rating-circle-bb": "BB",
                                    "esg-rating-circle-b": "B",
                                    "esg-rating-circle-ccc": "CCC",
                                    }
                        rating_section = bot.locate_element(class_name="ratingdata-container")
                        outer_circle = bot.locate_element(class_name="ratingdata-outercircle")
                        rating_div = bot.locate_element_within_element(outer_circle, class_name="ratingdata-company-rating")
                        class_str = rating_div.get_attribute("class")
                        esg_rating = next((rating for key, rating in rating_map.items() if key in class_str), "Unknown")
                        logging.info("ESG Rating: %s", esg_rating)

                        # Click Controversies toggle
                        controversies_toggle = bot.locate_element(id_name="esg-controversies-toggle-link")
                        controversies_toggle.click()
                        logging.info("Clicked controversies toggle")
                        sleep(5)

                        controversies_table = bot.locate_element(id_name="controversies-table")
                        env_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'column-controversy') and contains(text(), 'Environment')]")
                        social_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'column-controversy') and contains(text(), 'Social')]")
                        gov_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'column-controversy') and contains(text(), 'Governance')]")
                        customer_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Customers')]")
                        hr_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Human Rights')]")
                        labor_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Labor Rights')]")
                                    
                        output.append({
                                "MSCI_Company": company_name,
                                "MSCI_ESG_Rating": esg_rating,
                                "MSCI_Environment_Flag": get_flag_color(env_flag),
                                "MSCI_Social_Flag": get_flag_color(social_flag),
                                "MSCI_Governance_Flag": get_flag_color(gov_flag),
                                "MSCI_Customer_Flag": get_flag_color(customer_flag),
                                "MSCI_Human_Rights_Flag": get_flag_color(hr_flag),
                                "MSCI_Labor_Rights_Flag": get_flag_color(labor_flag)
                                })    
                                    
            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")
                continue
        return output
    except Exception as e:
        logging.error(f"Error with user agent {bot.user_agent}: {e}")
        return None
    finally:
        if 'bot' in locals():
            bot.driver.quit()

if __name__ == "__main__":
    Threader(msci_scraper, export_path)