"""This module provides utilities for database management module"""

import csv
import os
import sqlite3
import zipfile
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    filename='database_loading.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

DB_PATH = os.environ["DB_PATH"]

def create_empty_sqlite_db(db_path=None):
    """Creates an empty SQLite database at the specified path.

    Args:
        db_path (str): The file path where the SQLite database will be created.

    """
    if not db_path:
        db_path = DB_PATH

    # Check if the file already exists
    if Path(db_path).exists():
        raise FileExistsError(f"Database already exists at {db_path}")

    # Ensure the directory exists
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)

    # Close the connection immediately to keep it as an empty database
    conn.close()

    print(f"Database created at {db_path}")
    return True


def create_db_connection(db_path=None):
    """SQLite specific connection function takes in the db_path"""
    if not db_path:
        db_path = DB_PATH

    if not Path(db_path).exists():
        raise FileExistsError(f"Database does not exist at: {db_path}")

    conn = sqlite3.connect(db_path)
    return conn


def execute_sql_command(conn, sql_query):
    """Executes the given SQL command"""
    cur = conn.cursor()
    cur.execute(sql_query)
    conn.commit()
    return None


def create_csrhub_table(conn, table_name):
    """Create a table for scraped CSRHub data."""
    create_table_owned_stocks = f"""
    CREATE TABLE {table_name} (
        company TEXT NOT NULL,
        esg_score INTEGER,
        num_sources INTEGER
    )
    """
    execute_sql_command(conn, create_table_owned_stocks)


def create_lseg_table(conn, table_name):
    """Create a table for scraped LSEG data."""
    create_table_stocks = f"""
    CREATE TABLE {table_name} (
        company TEXT NOT NULL,
        esg_score TEXT,
        environment_score TEXT,
        social_score TEXT,
        government_score TEXT
    )
    """
    execute_sql_command(conn, create_table_stocks)


def create_msci_table(conn, table_name):
    """Create a table for scraped MSCI data."""
    create_table_stocks = f"""
    CREATE TABLE {table_name} (
        company TEXT NOT NULL,
        esg_score TEXT,
        environment_flag TEXT,
        social_flag TEXT,
        governance_flag TEXT,
        customer_flag TEXT,
        human_rights_flag TEXT,
        labor_rights_flag TEXT
    )
    """
    execute_sql_command(conn, create_table_stocks)

def create_spglobal_table(conn, table_name):
    """Create a table for scraped SPGlobal data."""
    create_table_stocks = f"""
    CREATE TABLE {table_name} (
        company TEXT NOT NULL,
        esg_score TEXT,
        country TEXT,
        industry TEXT,
        ticker TEXT,
        environment_score TEXT,
        social_score TEXT,
        governance_score TEXT
    )
    """
    execute_sql_command(conn, create_table_stocks)


def create_yahoo_table(conn, table_name):
    """Create a table for scraped Yahoo Finance data."""
    create_table_stocks = f"""
    CREATE TABLE {table_name} (
        company TEXT NOT NULL,
        market_cap TEXT,
        pe_ratio TEXT,
        eps TEXT,
        esg_score TEXT,
        environment_score TEXT,
        social_score TEXT,
        governance_score TEXT
    )
    """
    execute_sql_command(conn, create_table_stocks)


def load_csv_to_db(conn, data_dir, table_name, csv_file_name):
    """Load CSV files into an existing SQLite table.

    Args:
        conn: SQLite connection
        data_dir (str): Path to the directory containing CSV files
        table_name (str): Name of existing table
        csv_file_name (str): Name of CSV file to load

    Returns:
        bool: True if file is loaded successfully
    """
    cur = conn.cursor()

    if csv_file_name in os.listdir(data_dir):
        logging.info(f"Reading file: {csv_file_name}")
        file_path = os.path.join(data_dir, csv_file_name)
        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)  # Skip header row
            data_to_insert = [tuple(row) for row in reader]
            
            # Get number of columns from first row of data
            num_columns = len(data_to_insert[0]) if data_to_insert else 0
            placeholders = ','.join(['?' for _ in range(num_columns)])
                
            insert_query = f"""
                INSERT INTO {table_name} 
                VALUES ({placeholders})
                """
                
            cur.executemany(insert_query, data_to_insert)
            logging.info(f"Loaded data from {csv_file_name} into {table_name}")
    else:
        raise FileNotFoundError(f"CSV file not found: {csv_file_name}")
    conn.commit()
    return True


def create_tables_and_load_data(data_path, csrhub_table_name, 
                                lseg_table_name, msci_table_name,
                                spglobal_table_name, yahoo_table_name):
    """Creates accounts, stocks_owned, and stocks tables and loads data"""
    conn = create_db_connection()

    # Mapping of table names to their corresponding table creation functions and csv file names
    table_config = {
        csrhub_table_name: (create_csrhub_table, "csrhub_scores.csv"),
        lseg_table_name: (create_lseg_table, "lseg_esg_scores.csv"),
        msci_table_name: (create_msci_table, "msci_esg_scores.csv"),
        spglobal_table_name: (create_spglobal_table, "spglobal_esg_scores.csv"),
        yahoo_table_name: (create_yahoo_table, "yahoo_esg_scores.csv")
    }

    # Iterate through the configuration and create tables
    for table_name, (create_table_func, csv_file_name) in table_config.items():
        create_table_func(conn, table_name)
        load_csv_to_db(conn, data_path, table_name, csv_file_name)


def rm_db(db_path=None):
    """Delete the Database file not recoverable, be careful"""
    if not db_path:
        db_path = DB_PATH

    if Path(db_path).exists():
        Path.unlink(db_path)

    print(f"Database at {db_path} removed")

    return None
