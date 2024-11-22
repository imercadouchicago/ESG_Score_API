[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/EqWXl6Ay)

App Structure:

- esg_app
    -- api
        --- data
            ---- SP500.csv
        --- test_project.py

    -- utils
        --- __init__.py
        --- scraper.py
        
- README.md
- requirements.txt
- docker-compose.yml
- Makefile
- Dockerfile
- app.py

How to Use:

1. In the terminal, run "make flask" to build Docker image and run the Flask app.
2. Go to http://0.0.0.0:5001/selenium-test to test Flask route and ability to run Selenium's Chrome webdriver in image.

1. In the terminal, run "make interactive" to build Docker image and run interact sh shell.
2. Run "PYTHONPATH=/app/src python esg_app/api/test.py" in interactive shell to test Webscraper class.

Cite Sources:

- https://github.com/tonyp7/docker-flask-selenium-chromedriver/tree/main
- https://github.com/shweta-29/Companies_ESG_Scraper/blob/main/README.md
- https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks?resource=download&select=sp500_companies.csv

Note:

The code within the current repository is aggregated from the above sources.