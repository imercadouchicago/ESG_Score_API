''' This module contains utility functions for the routes. '''

from flask import jsonify
from utils.data_utils.loading_utils import create_db_connection

def execute_query_return_list_of_dicts_lm(conn, sql_query, params):
    """Executes SQL query with parameters and returns result

    Args:
        conn: [sqlite3.Connection] connection to the database
        sql_query: [str] SQL query to execute
        params: [tuple] parameters to pass to the SQL query

    Returns:
        [list]: list of dictionaries representing the result of the query
    """
    cursor = conn.cursor()
    cursor.execute(sql_query, params)
    description_info = cursor.description

    headers = [x[0] for x in description_info]
    return_dict_list = []

    while True:
        single_result = cursor.fetchone()

        if not single_result:
            break

        single_result_dict = dict(zip(headers, single_result))
        return_dict_list.append(single_result_dict)

    return return_dict_list

def validate_table_name(table_name):
    """Validates the table name

    Args:
        table_name: [str] name of the table to validate

    Returns:
        [bool]: True if the table name is valid, False otherwise
    """
    valid_tables = ["csrhub_table", "lseg_table", "msci_table", "spglobal_table", "yahoo_table"]
    if table_name not in valid_tables:
        return False
    return True

def get_table(table_name):
    """Returns the entire table as a JSON response

    Args:
        table_name: [str] name of the table to query

    Returns:
        [dict]: entire table as a JSON response
    """
    # Validate the table name
    if not validate_table_name(table_name):
        return jsonify({"error": "Invalid table name"}), 400
    
    # Build the SQL query
    query = f"SELECT * FROM {table_name}"

    # Create the DB connection and execute the query
    conn = create_db_connection()
    result = execute_query_return_list_of_dicts_lm(conn, query, ())

    # If no data is found, return a 404 error
    if not result:
        return jsonify({"error": "Table not found"}), 404

    return jsonify(result), 200

def get_company_from_table(table_name, ticker):
    """Returns the company data from the table with the given name in JSON format.

    Args:
        table_name: [str] name of the table to query
        ticker: [str] ticker of the company to query

    Returns:
        [dict]: company data from the table in JSON format
    """
    # Validate the table name
    if not validate_table_name(table_name):
        return jsonify({"error": "Invalid table name"}), 400
    
    # Build the SQL query
    query = f"SELECT * FROM {table_name} WHERE company = ?"

    # Create the DB connection and execute the query
    conn = create_db_connection()
    result = execute_query_return_list_of_dicts_lm(conn, query, (ticker,))

    # If no data is found, return a 404 error
    if not result:
        return jsonify({"error": "Company not found"}), 404

    return jsonify(result), 200

def get_company_scores(ticker):
    """Returns the ESG scores from all tables for a company in JSON format.

    Args:
        ticker: [str] ticker of the company to query

    Returns:
        [dict]: ESG scores from all tables for a company in JSON format
    """
    tables = ["csrhub_table", "lseg_table", "msci_table", "spglobal_table", "yahoo_table"]
    result = {}

    conn = create_db_connection()
    cursor = conn.cursor()
    for table in tables:
        query = f"SELECT esg_score FROM {table} WHERE company = ?"
        cursor.execute(query, (ticker,))
        
        while True:
            single_result = cursor.fetchone()
            if not single_result:
                break
            result[table] = single_result[0]

    return jsonify(result), 200
    