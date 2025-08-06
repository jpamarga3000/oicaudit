# audit_tool/backend/split_trnm_data_by_branch.py
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
# FIX: Import specific SQLAlchemy types
from sqlalchemy.types import VARCHAR, DATE, DECIMAL, TEXT
# Removed: from sqlalchemy.dialects import mysql
# Removed: from sqlalchemy.dialects.mysql import base as mysql_base
import traceback

# Add the project root to sys.path to enable absolute imports
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db_common import get_db_connection_sqlalchemy

# --- Configuration ---
SOURCE_TABLE_NAME = 'trnm_data' # Your current large table
TARGET_TABLE_PREFIX = 'trnm_' # New tables will be trnm_aglayan, trnm_bulua, etc.

# Define the schema for the new branch-specific tables.
# This should match the schema of your existing trnm_data table.
TABLE_SCHEMA_MAPPING = {
    'TRN': VARCHAR(255),
    'ACC': VARCHAR(255),
    'TRNTYPE': VARCHAR(255),
    'TLR': VARCHAR(255),
    'LEVEL': VARCHAR(255),
    'TRNDATE': DATE,
    'TRNAMT': DECIMAL(18, 2),
    'TRNNONC': DECIMAL(18, 2),
    'TRNINT': DECIMAL(18, 2),
    'TRNTAXPEN': DECIMAL(18, 2),
    'BAL': DECIMAL(18, 2),
    'SEQ': VARCHAR(255),
    'TRNDESC': TEXT,
    'APPTYPE': VARCHAR(255),
    'Branch': VARCHAR(255) # Keep Branch column in new tables for consistency/flexibility
}

def create_trnm_branch_table_if_not_exists(engine, table_name, schema_map):
    """
    Creates a new MySQL table for a specific branch if it doesn't already exist,
    using the provided schema map.
    """
    column_defs = []
    
    for col_name, sql_type in schema_map.items():
        # FIX: Get SQL type string directly based on SQLAlchemy type instance
        if isinstance(sql_type, VARCHAR):
            type_str = f"VARCHAR({sql_type.length})"
        elif isinstance(sql_type, DECIMAL):
            type_str = f"DECIMAL({sql_type.precision}, {sql_type.scale})"
        elif isinstance(sql_type, DATE):
            type_str = "DATE"
        elif isinstance(sql_type, TEXT):
            type_str = "TEXT"
        else:
            # Fallback for other types, might need more specific handling if new types are added
            type_str = str(sql_type) 
        
        column_defs.append(f"`{col_name}` {type_str}")
    
    # You might want to add a PRIMARY KEY here for better performance and data integrity.
    # Example composite primary key (adjust based on your data's uniqueness):
    # column_defs.append("PRIMARY KEY (`Branch`, `TRNDATE`, `ACC`, `SEQ`)")
    
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        {', '.join(column_defs)}
    );
    """
    
    try:
        print(f"  Attempting to create table with SQL:\n{create_table_sql}") # Debug print
        with engine.connect() as connection:
            connection.execute(text(create_table_sql))
            connection.commit()
        print(f"  Table '{table_name}' ensured to exist.")
        return True
    except Exception as e:
        print(f"  Error creating table '{table_name}': {e}")
        traceback.print_exc()
        return False

def split_data_by_branch():
    """
    Connects to MySQL, reads data from SOURCE_TABLE_NAME, and splits it into
    branch-specific tables (trnm_branchname) in the same database.
    """
    print(f"Starting data splitting from '{SOURCE_TABLE_NAME}' into branch-specific tables.")

    engine = get_db_connection_sqlalchemy()
    if engine is None:
        print("Error: SQLAlchemy engine is not initialized. Aborting data splitting.")
        return

    try:
        # 1. Get all unique branches from the source table
        print(f"Fetching unique branches from '{SOURCE_TABLE_NAME}'...")
        branches_df = pd.read_sql(f"SELECT DISTINCT Branch FROM `{SOURCE_TABLE_NAME}` WHERE Branch IS NOT NULL AND Branch != ''", engine)
        unique_branches = [str(b).strip().lower() for b in branches_df['Branch'].tolist()]
        
        if not unique_branches:
            print(f"No unique branches found in '{SOURCE_TABLE_NAME}'. Nothing to split.")
            return

        print(f"Found {len(unique_branches)} unique branches: {', '.join(unique_branches)}")

        total_rows_moved = 0
        
        for branch_name_lower in unique_branches:
            target_table_name = f"{TARGET_TABLE_PREFIX}{branch_name_lower}"
            print(f"\nProcessing branch '{branch_name_lower.upper()}' -> Target Table: '{target_table_name}'")

            # Create the target table if it doesn't exist
            if not create_trnm_branch_table_if_not_exists(engine, target_table_name, TABLE_SCHEMA_MAPPING):
                print(f"Skipping branch '{branch_name_lower.upper()}' due to table creation failure.")
                continue

            # Fetch data for the current branch from the source table
            print(f"  Fetching data for '{branch_name_lower.upper()}' from '{SOURCE_TABLE_NAME}'...")
            branch_data_query = f"SELECT * FROM `{SOURCE_TABLE_NAME}` WHERE Branch = '{branch_name_lower.upper()}'"
            # Use branch_df for the data read from the database
            branch_df = pd.read_sql(branch_data_query, engine)

            if branch_df.empty:
                print(f"  No data found for branch '{branch_name_lower.upper()}' in '{SOURCE_TABLE_NAME}'.")
                continue

            # Ensure column names are uppercase to match schema mapping
            branch_df.columns = [col.upper() for col in branch_df.columns]

            # Ensure the DataFrame to import matches the target schema columns and types
            # This reindex will add missing columns as NaN if not present in branch_df
            df_to_import = branch_df.reindex(columns=list(TABLE_SCHEMA_MAPPING.keys()))
            
            # Perform explicit type conversions for SQLAlchemy to_sql
            # FIX: Apply conversions to df_to_import itself, not the original 'df' (which is branch_df here)
            for col_name, sql_type in TABLE_SCHEMA_MAPPING.items():
                if col_name in df_to_import.columns:
                    if isinstance(sql_type, DECIMAL):
                        df_to_import[col_name] = pd.to_numeric(df_to_import[col_name], errors='coerce').fillna(0)
                    elif isinstance(sql_type, DATE):
                        # Convert to datetime, then to date objects
                        df_to_import[col_name] = pd.to_datetime(df_to_import[col_name], errors='coerce').dt.date
                    else: # For VARCHAR, TEXT
                        df_to_import[col_name] = df_to_import[col_name].astype(str).fillna('')

            # Insert data into the branch-specific table
            try:
                # Use 'replace' if you want to clear and re-insert for each run,
                # or 'append' if you're sure you only run once or handle duplicates.
                # For splitting, 'replace' is safer if you might re-run the split.
                df_to_import.to_sql(
                    name=target_table_name,
                    con=engine,
                    if_exists='replace', # 'replace' will drop table if exists and recreate
                    index=False,
                    dtype=TABLE_SCHEMA_MAPPING
                )
                print(f"  Successfully moved {len(df_to_import)} rows to '{target_table_name}'.")
                total_rows_moved += len(df_to_import)
            except Exception as e:
                print(f"  Error moving data to '{target_table_name}': {e}")
                traceback.print_exc()

        print(f"\nData splitting complete. Total rows moved: {total_rows_moved}")
        
        # Optional: Delete data from the original trnm_data table after successful split
        # WARNING: Only uncomment and run this if you are absolutely sure all data
        # has been successfully moved to the new tables and you no longer need trnm_data.
        # with engine.connect() as connection:
        #     connection.execute(text(f"TRUNCATE TABLE `{SOURCE_TABLE_NAME}`"))
        #     connection.commit()
        # print(f"Original table '{SOURCE_TABLE_NAME}' truncated.")

    except Exception as e:
        print(f"An error occurred during data splitting: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    # You would run this script from your terminal:
    # python audit_tool/backend/split_trnm_data_by_branch.py
    split_data_by_branch()
