# ESG Score API

## Overview
A comprehensive web application for collecting, aggregating, and querying Environmental, Social, and Governance (ESG) scores from multiple major providers:
- CSRHub
- LSEG
- MSCI
- S&P Global
- Yahoo Finance

## Features

The folder 'esg_backend' contains the backend of the web application, which contains its own Dockerfile and Makefile. The backend is built using Flask, runs on a Gunicorn server, and is containerized with Docker.

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
Each of the csv files have been loaded into a separate SQL table within the SQLite database 'esg_scores.db' using the commands created in 'data_utils/db_manage.py' and the helper functions associated with these commands in 'data_utils/loading_utils.py'.

The file 'app.py' builds a Flask app with the api endpoints located in 'routes/routes.py' and the helper functions 
associated with these endpoints located in 'route_utils/route_utils.py'. These endpoint helper functions query the SQL tables 
within the SQLite database. 

The folder 'esg_frontend' contains the React frontend for the web application and its own Dockerfile.

## Technology Stack
- Python
- Makefile
- Docker
- React
- Flask
- Selenium WebDriver
- Concurrent Futures 
- SQLite
- A variety of Python packages

## Project Structure
```
ESG_SCORE_API/
├── esg_backend/
│   ├── api/
│   │   ├── data/
│   │   │   ├── esg_scores.db
│   │   │   ├── SP500.csv
│   │   │   ├── lseg_esg_scores.csv
│   │   │   ├── msci_esg_scores.csv
│   │   │   ├── spglobal_esg_scores.csv
│   │   │   ├── csrhub_esg_scores.csv
│   │   │   └── yahoo_esg_scores.csv
│   ├── esg_scrapers/
│   │   ├── csrhub_nonthreaded.py
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
│   │   │   ├── cleaning_utils.py
│   │   │   ├── scraper.py
│   │   │   └── threader.py
│   ├── app.py
│   ├── Dockerfile
│   ├── Makefile
│   └── requirements.txt
├── esg_frontend/
│   ├── public/
│   ├── src/
│   │   ├── Components/
│   │   │   ├── CompanyTableDataFetcher.js
│   │   │   ├── ESGDataFetcher.js
│   │   │   └── TableFetcher.js
│   │   ├── App.js
│   │   ├── index.css
│   │   └── index.js
│   ├── Dockerfile
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   └── tailwind.config.js
├── docker-compose.yml
├── Makefile
├── Methodology
└── README.md
```

## Setup

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/

2. Clone the repository:

```bash
git clone https://github.com/yourusername/esg_score_api.git
```

3. Interact with the Docker containers using the make commands contained in the Makefiles. See the section below for more information.

## Interacting with the Web Application
The Makefile within the root of the repository contains a command to run the web application. The make command "make prod" will run the docker-compose.yml file, which will build the backend and frontend containers and run the web application on port 3000.

```bash
cd ESG_SCORE_API
ESG_SCORE_API $ make prod
```

## Interacting with the API and Scrapers
The Makefile within the 'esg_backend' folder contains commands that can be used to test, replicate, and interact with every aspect of the API and scrapers. 
All make commands include a dependency on the make build command, which allows the user to run every command without having to first run `make build`.

### Docker Commands

```bash
# Build the Docker container
esg_backend $ make build 

# Run the container interactively
esg_backend $ make interactive 
```

### Scraper Commands
Each ESG provider has its own scraper module that can be run independently using the following commands.
The export paths in each of the scraper modules has already been changed so that the existing data will not be overwritten. 
The dataframe number of rows has been set to 4 in the Threader function so the scrapers can be tested efficiently. 
If you would like to test the scrapers, then feel free to run the following commands.

```bash
esg_backend $ make csrhub
esg_backend $ make lseg
esg_backend $ make msci
esg_backend $ make spglobal
esg_backend $ make yahoo
```

### Database Commands

```bash
# Create a sqlite database file and associated tables
esg_backend $ make db_create 

# Load data into the created sqlite database
esg_backend $ make db_load 

# Delete the created database file
esg_backend $ make db_rm 

# Delete the created database file and reload data
esg_backend $ make db_clean 

# Create interactive sqlite session with database
esg_backend $ make db_interactive 
```

### Flask Command
To build the Flask app and run on port 5001:

```bash
esg_backend $ make flask
```

## Flask API Routes

Note: For the following routes, the table name must be one of the following: 
`csrhub_table`, `lseg_table`, `msci_table`, `spglobal_table`, `yahoo_table`, `sp500_table`.

If running on port 5001, the base URL will be http://0.0.0.0:5001/.

1. [GET] Returns the specified table in JSON format.

    URL: `esg_api/<string:table_name>`

2. [GET] Returns the specified company's data from the specified table in JSON format.

    URL: `esg_api/<string:table_name>/<string:ticker>`

3. [GET] Returns the ESG scores from all tables for a specified company in JSON format.

    URL: `esg_api/all_tables/<string:ticker>`

## Data Sources
The sp500.csv file: 

- https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks?resource=download&select=sp500_companies.csv

CSRHub data: 

- https://www.csrhub.com/search/name/

LSEG data: 

- https://www.lseg.com/en/data-analytics/sustainable-finance/esg-scores

MSCI data: 

- https://www.msci.com/our-solutions/esg-investing/esg-ratings-climate-search-tool

SP Global data: 

- https://www.spglobal.com/esg/scores/

Yahoo Finance data: 

- https://finance.yahoo.com/lookup/

## Contact
Isabella Mercado - imercado@uchicago.edu

Lucas Kopinski - lkopinski@uchicago.edu

Project Link: https://github.com/imercadouchicago/esg_score_api
```
