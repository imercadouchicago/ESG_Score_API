"""This module provides for database management utilies"""

import argparse
import os

from loading_utils import (
    create_tables_and_load_data,
    create_empty_sqlite_db,
    rm_db,
)

DATA_DIR = os.environ["DATA_DIR"]

if __name__ == "__main__":
    command_list = ["db_create", "db_load", "db_rm", "db_clean"]
    parser = argparse.ArgumentParser(description="Manage the SQLite database.")

    parser.add_argument(
        "command", choices=command_list, help="Command to execute"
    )

    args = parser.parse_args()
    csrhub_table_name = "csrhub_table"
    lseg_table_name = "lseg_table"
    msci_table_name = "msci_table"
    spglobal_table_name = "spglobal_table"
    yahoo_table_name = "yahoo_table"


    if args.command == "db_create":
        create_empty_sqlite_db()
    if args.command == "db_load":
        create_tables_and_load_data(DATA_DIR, csrhub_table_name, 
                                    lseg_table_name , msci_table_name,
                                    spglobal_table_name, yahoo_table_name)
    if args.command == "db_rm":
        rm_db()
    if args.command == "db_clean":
        rm_db()
        create_empty_sqlite_db()
        create_tables_and_load_data(DATA_DIR, csrhub_table_name, 
                                    lseg_table_name , msci_table_name,
                                    spglobal_table_name, yahoo_table_name)
