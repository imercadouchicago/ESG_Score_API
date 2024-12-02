from esg_app.utils.route_utils.route_utils import (get_table,
                                                   get_company_from_table,
                                                   get_company_scores)

BASE_URL="/esg_api"

def all_routes(app):
    @app.route('/', methods=['GET'])
    def home():
        return "Welcome to the ESG API!"
    
    @app.route(f'{BASE_URL}/<string:table_name>', methods=['GET'])
    def get_table_by_name(table_name):
        """Returns the table with the given name in JSON format.

        See get_table docstring for more information for args and returns.
        """
        return get_table(table_name)
    
    @app.route(f'{BASE_URL}/<string:table_name>/<string:ticker>', methods=['GET'])
    def get_company_data_from_table(table_name, ticker):
        """Returns the company data from the table with the given name in JSON format.

        See get_company_data_from_table docstring for more information for args and returns.
        """
        return get_company_from_table(table_name, ticker)
    
    @app.route(f'{BASE_URL}/all_tables/<string:ticker>', methods=['GET'])
    def get_company_scores_from_tables(ticker):
        """Returns the ESG scores from all tables for a company in JSON format.

        See get_company_scores docstring for more information for args and returns.
        """
        return get_company_scores(ticker)
