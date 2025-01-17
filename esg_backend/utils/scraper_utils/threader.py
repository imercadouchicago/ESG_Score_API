''' This module contains a function for applying multithreading to selenium-based webscraping functions.'''

from queue import Queue
import numpy as np
import pandas as pd
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Callable 
from threading import Lock

import_path = 'esg_backend/api/data/SP500.csv'
USER_AGENTS = [
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

# Configure logging
logging.basicConfig(
    filename='parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def Threader(website_function: Callable, export_path: str, missing_companies: list = None):
    '''
    This function using multithreading for running webscraper functions in parallel 
    and aggregates and exports results from each thread to a csv.

    Args:
        website_function:  [callable] The function used to webscrape a website.
        export_path: [str] The path for the exported csv.
        missing_companies: [list] A list of companies missed when initially ran Threader.
    '''
    logging.info("Script started")
    
    # Create queue with user agents
    user_agents = Queue()
    for agent in USER_AGENTS:
        user_agents.put(agent)

    try: 
        if missing_companies is not None:
            # If missing_companies list provided, then assign name 'df' to list
            logging.info(f"Processing {len(missing_companies)} missing companies")
            df = missing_companies
        else: 
            logging.info("Reading input data from: %s", import_path)
            df = pd.read_csv(import_path)
            df = df.head(4)
            logging.info("Data loaded successfully. Number of records: %d", len(df))
    except FileNotFoundError as e:
        logging.error("Input file not found. Error: %s", e)
        return

    # Calculate number of threads
    num_threads = min(len(df), user_agents.qsize())
    
    # Create non-overlapping chunks based on number of threads
    df_chunks = np.array_split(df, num_threads)
    
    # Create shared set for tracking processed companies
    processed_tickers = set()
    lock = Lock()

    try:
        # Inform threadpoolexecutor of number of threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Assign each thread a chunk
            futures = [executor.submit(website_function, chunk, user_agents, processed_tickers, lock) 
                      for chunk in df_chunks]
            
            # Store results from threads executing function on assigned chunk
            results = []
            for future in concurrent.futures.as_completed(futures):
                batch_results = future.result()
                if batch_results:
                    results.extend(batch_results)

        # Create pandas dataframe with results and export to csv
        if results:
            results_df = pd.DataFrame(results)
            results_df.to_csv(export_path, index=False)
            logging.info(f"Successfully saved {len(results_df)} results")
        else:
            logging.warning("No results to save")
    
    except Exception as e:
        logging.error(f"Main process error: {e}")

    logging.info("Script completed")