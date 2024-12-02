# ESG Score API

## Overview
A comprehensive Docker-based API for collecting, aggregating, and querying Environmental, Social, and Governance (ESG) scores from multiple major providers:
- CSRHub
- LSEG
- MSCI
- S&P Global
- Yahoo Finance

## Features
The folder 'esg_scrapers' contains a scraper module for each of the 5 ESG score providers above.
These modules rely on the util files within the 'scraper_utils' folder and contain the following features:
- Multi-threaded Selenium web scraping for efficient data collection
- Thread locking to keep track of processed companies
- A queue system to assign each thread to a unique user agent
- Automated cookie handling and browser management
- Robust error handling and retry mechanisms
- Detailed logging system

The folder 'data' contains csv files with the raw esg data aggregated by running each of the scraper modules 
on the list of companies in the file 'sp500.csv' (which contains the S&P 500 companies).
Each of the csv files have been loaded into a separate SQL table within the SQLite database 'esg_scores.db' using the commands created in 'data_utils/db_manage.py' with the helper functions associated with these commands in 'data_utils/loading_utils.py'.

The file 'app.py' builds a Flask app with the api endpoints located in 'routes/routes.py' and the helper functions 
associated with these endpoints located in 'route_utils/route_utils.py'. These endpoint helper functions query the SQL tables 
within the SQLite database. 

## Technology Stack
- Python
- Makefile
- Docker
- Flask
- Selenium WebDriver
- Concurrent Futures 
- SQLite
- A variety of Python packages

## Project Structure
```
esg_app/
├── api/
│   ├── data/
│   │   ├── esg_scores.db
│   │   ├── SP500.csv
│   │   ├── lseg_esg_scores.csv
│   │   ├── msci_esg_scores.csv
│   │   ├── spglobal_esg_scores.csv
│   │   ├── csrhub_esg_scores.csv
│   │   └── yahoo_esg_scores.csv
│   ├── draft_scrapers/
│   ├── esg_scrapers/
│   │   ├── csrhub.py
│   │   ├── lseg_threaded.py
│   │   ├── msci_threaded.py
│   │   ├── spglobal_threaded.py
│   │   └── yahoo_threaded.py
│   └── routes/
│   │   ├── routes.py
│   ├── logging_files/
│   └── utils/
│   │   ├── data_utils/
│   │   │   ├── db_manage.py
│   │   │   └── loading_utils.py
│   │   ├── route_utils/
│   │   │   └── route_utils.py
│   │   └── scraper_utils/
│   │   │   ├── msci_utils.py
│   │   │   ├── original_scraper.py
│   │   │   ├── scraper.py
│   │   │   └── threader.py
├── app.py
├── Dockerfile
├── Makefile
├── README.md
└── requirements.txt
```

## Setup

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/

2. Clone the repository:

```bash
git clone https://github.com/yourusername/esg_score_api.git
cd esg_score_api
```

3. Interact with the Docker container using the make commands contained in the Makefile:

```bash
esg_score_api $ make <command>
```

## Usage
The Makefile contains commands that can be used to test, replicate, and interact with every aspect of the API. 
All make commands include a dependency on the make build command, which allows the user to run every command without having to first run `make build`.

### Docker Commands

```bash
# Build the Docker container
esg_score_api $ make build 

# Run the container interactively
esg_score_api $ make interactive 
```

### Scraper Commands
Each ESG provider has its own scraper module that can be run independently using the following commands.
The export paths in each of the scraper modules has already been changed so that the existing data will not be overwritten. 
The dataframe number of rows has been set to 1 in the Threader function so the scrapers can be tested efficiently. 
If you would like to test the scrapers, then feel free to run the following commands.

```bash
esg_score_api $ make csrhub
esg_score_api $ make lseg
esg_score_api $ make msci
esg_score_api $ make spglobal
esg_score_api $ make yahoo
```

### Database Commands

```bash
# Create a sqlite database file and associated tables
esg_score_api $ make db_create 

# Load data into the created sqlite database
esg_score_api $ make db_load 

# Delete the created database file
esg_score_api $ make db_rm 

# Delete the created database file and reload data
esg_score_api $ make db_clean 

# Create interactive sqlite session with database
esg_score_api $ make db_interactive 
```

### Flask Command
To build the Flask app and run on port 5001:

```bash
esg_score_api $ make flask
```

## Flask API Routes

Note: For the following routes, the table name must be one of the following: 
`csrhub_table`, `lseg_table`, `msci_table`, `spglobal_table`, `yahoo_table`, `sp500_table`.

If running on port 5001, the base URL will be http://0.0.0.0:5001/.

1. [GET] Returns the table with the given name in JSON format.

    URL: `esg_api/<string:table_name>`

2. [GET] Returns the company data from the table with the given name in JSON format.

    URL: `esg_api/<string:table_name>/<string:ticker>`

3. [GET] Returns the ESG scores from all tables for a company in JSON format.

    URL: `esg_api/all_tables/<string:ticker>`

## Acknowledgments
The sp500.csv data was sourced from:
- https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks?resource=download&select=sp500_companies.csv

The original_scraper.py file was adapted from:
- https://github.com/shweta-29/Companies_ESG_Scraper

## Contact
Isabella Mercado - imercado@uchicago.edu

Lucas Kopinski - lkopinski@uchicago.edu

Project Link: https://github.com/imercadouchicago/esg_score_api
```
