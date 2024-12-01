import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from esg_app.utils.scraper import WebScraper
import logging
from time import sleep
import subprocess
import os

# Configure logging
logging.basicConfig(
    filename='/app/src/parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# # Set up Xvfb for one instance
# def start_xvfb():
#     logging.info("Starting Xvfb...")
#     # Start Xvfb on display :1
#     subprocess.Popen(['Xvfb', ':1', '-screen', '0', '1024x768x16'])
#     os.environ['DISPLAY'] = ':1'
#     logging.info("Xvfb started on display :1")

def scrape_company(company):
    bot = WebScraper("https://www.spglobal.com/esg/scores/")
    try:
        bot.accept_cookies('//*[@id="onetrust-accept-btn-handler"]')
        search_bar = bot.send_request_to_search_bar(
            bot.headername, pd.DataFrame.from_records([company]), 0, class_name='banner-search__input')
        search_bar.send_keys(Keys.RETURN)
        bot.wait_element_to_load('//*[@id="company-name"]')

        ESG_Company = bot.locate_element(xpath='//*[@id="company-name"]')
        ESG_Score = bot.locate_element(class_name="scoreModule__score")
        ESG_Country = bot.locate_element('//*[@id="company-country"]')
        ESG_Industry = bot.locate_element('//*[@id="company-industry"]')
        ESG_Ticker = bot.locate_element('//*[@id="company-ticker"]')

        return {
            "SnP_ESG_Company": ESG_Company.text,
            "SnP_ESG_Score": ESG_Score.text,
            "SnP_ESG_Country": ESG_Country.text,
            "SnP_ESG_Industry": ESG_Industry.text,
            "SnP_ESG_Ticker": ESG_Ticker.text,
        }
    except Exception as e:
        logging.error(f"Error processing company {company}: {e}")
        return None
    finally:
        bot.driver.quit()

if __name__ == "__main__":
    print("Script Started.")
    logging.info("Script started.")
    
    # # Start Xvfb for the first instance
    # start_xvfb()

    try:
        df = pd.read_csv("esg_app/api/data/SP500.csv")
        df = df.head(1)  # Just scrape the first company for now
        logging.info("Successfully loaded input data.")
    except FileNotFoundError as e:
        logging.error("Input file not found.")
        raise e

    # Scrape for one company to test Xvfb functionality
    logging.info("Starting scraping for one company...")
    result = scrape_company(df.iloc[0])

    # Save results
    if result:
        pd.DataFrame([result]).to_csv('esg_app/api/data/SP500_esg_scores.csv', index=False)

    logging.info("Scraping completed.")

# Dockerfile:
# RUN apk add --no-cache \
#     chromium \
#     chromium-chromedriver \
#     libx11 \
#     libxcomposite \
#     libxrandr \
#     libxi \
#     libxdamage \
#     libxfixes \
#     mesa-dri-gallium \
#     mesa-egl \
#     ttf-freefont \
#     fontconfig \
#     harfbuzz \
#     nss \
#     xvfb \
#     xvfb-run

# Use BuildKit cache mounts for pip and requirements.txt file
# RUN --mount=type=cache,target=/root/.cache/pip \
#     --mount=type=bind,source=requirements.txt,target=requirements.txt \
#     python -m pip install -r requirements.txt

# USER root
# # Add a startup script to ensure proper permissions
# COPY entrypoint.sh /app/src/entrypoint.sh
# RUN chmod +x /app/src/entrypoint.sh

# # Set the entrypoint to the script
# ENTRYPOINT ["/app/src/entrypoint.sh"]

# Makefile:
# snpglobal: build
# 	docker run -it --rm \
# 	-e PYTHONPATH='/app/src' \
# 	-v $(LOCAL_HOST_DIR):$(CONTAINER_SRC_DIR) \
# 	$(IMAGE_NAME) /bin/sh -c \
# 	"xvfb-run -a python esg_app/utils/parallel_scraper.py"