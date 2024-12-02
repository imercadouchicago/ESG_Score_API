# ESG Score API

## Overview
A comprehensive API for collecting, aggregating, and querying Environmental, Social, and Governance (ESG) scores from multiple major providers:
- CSRHUB
- LSEG
- MSCI
- S&P Global
- Yahoo Finance

## Features
- Multi-threaded web scraping for efficient data collection
- Automated cookie handling and browser management
- Robust error handling and retry mechanisms
- Detailed logging system
- SQLite database integration
- Flask API for querying data
- Support for S&P 500 companies

## Technology Stack
- Python
- Makefile
- Docker
- Flask
- Selenium WebDriver
- Concurrent Futures
- SQLite
- (other packages)

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
├── docker-compose.yml
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

3. Interact with Docker using the Makefile:

```bash
esg_score_api $ make <command>
```

## Usage

### Docker Commands

```bash
esg_score_api $ make build # Build the Docker container
esg_score_api $ make interactive # Build and run the container interactively
```

### Scraper Commands
Each ESG provider has its own scraper module that can be run independently.

```bash
esg_score_api $ make csrhub
esg_score_api $ make lseg
esg_score_api $ make msci
esg_score_api $ make spglobal
esg_score_api $ make yahoo
```

### Database Commands

```bash
esg_score_api $ make db_create # Create a sqlite database file and associated tables
esg_score_api $ make db_load # Load data into the sqlite database
esg_score_api $ make db_rm # Delete the database file
esg_score_api $ make db_clean # Delete the database file and reload data
esg_score_api $ make db_interactive # Create interactive sqlite session with database
```

### Flask Command
To build the Flask app and run on port 5001:

```bash
esg_score_api $ make flask
```

## Flask API Routes

Note: For the following routes, the table name must be one of the following: 
`csrhub_table`, `lseg_table`, `msci_table`, `spglobal_table`, `yahoo_table`, `sp500_table`.

1. [GET] Returns the table with the given name in JSON format.

URL: `/esg_api/<string:table_name>`

2. [GET] Returns the company data from the table with the given name in JSON format.

URL: `/esg_api/<string:table_name>/<string:ticker>`

3. [GET] Returns the ESG scores from all tables for a company in JSON format.

URL: `/esg_api/all_tables/<string:ticker>`

## Acknowledgments
The docker-compose.yml file was sourced from:
- https://github.com/tonyp7/docker-flask-selenium-chromedriver/tree/main
The sp500.csv data was sourced from:
- https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks?resource=download&select=sp500_companies.csv
The original_scraper.py file was adapted from:
- https://github.com/shweta-29/Companies_ESG_Scraper/blob/main/README.md

## Contact
Isabella Mercado - imercado@uchicago.edu
Lucas Kopinski - lkopinski@uchicago.edu
Project Link: https://github.com/imercado/esg_score_api
```
