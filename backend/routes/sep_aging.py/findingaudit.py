import pandas as pd
import pymysql.cursors
import os
import numpy as np

# ==============================================================================
# Database Configuration
# ==============================================================================
# Your MySQL database connection details.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Your MySQL password
    'database': 'dc_req_db',
    'charset': 'utf8mb4'
}

# ==============================================================================
# Main Functions
# ==============================================================================

def create_or_check_table(cursor, table_name, columns_info):
    """
    Checks if a table exists, and creates it if it doesn't.
    Args:
        cursor: The database cursor object.
        table_name (str): The name of the table to check/create.
        columns_info (list): A list of tuples containing column name and data type.
    """
    try:
        # Check if the table exists
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print(f"Table '{table_name}' not found. Creating table...")
            
            # Construct the CREATE TABLE statement dynamically
            column_definitions = [f"`{col[0]}` {col[1]}" for col in columns_info]
            create_table_sql = f"""
            CREATE TABLE `{table_name}` (
                `Id` INT NOT NULL AUTO_INCREMENT,
                {', '.join(column_definitions)},
                PRIMARY KEY (`Id`)
            );
            """
            cursor.execute(create_table_sql)
            print(f"Table '{table_name}' created successfully.")
        else:
            print(f"Table '{table_name}' already exists. Data will be appended.")

    except pymysql.MySQLError as e:
        print(f"Database error during table creation/check: {e}")
        raise

def upload_data_from_csv(file_path, table_name, required_columns):
    """
    Reads data from a CSV file and uploads it to the specified MySQL table.
    
    Args:
        file_path (str): The path to the CSV file.
        table_name (str): The name of the table to insert data into.
        required_columns (list): A list of column names expected in the CSV.
    """
    print(f"Attempting to upload data from file: {file_path}")

    if not os.path.exists(file_path) or os.path.isdir(file_path):
        print(f"Error: The provided path '{file_path}' is invalid or is not a file. Please enter the full path to a CSV file.")
        return

    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Define column information for the `finding_audit` table with new headers
        column_definitions = [
            ('Code', 'VARCHAR(255)'),
            ('Branch', 'VARCHAR(255)'),
            ('Year', 'INT'),
            ('Risk_ID', 'INT'),
            ('Finding_ID', 'INT'),
            ('Status', 'VARCHAR(255)'),
            ('Date_Updated', 'DATE'),
            ('Audit_Remarks', 'TEXT'),
            ('Verified_By', 'VARCHAR(255)')
        ]

        # Check for table existence and create if necessary
        create_or_check_table(cursor, table_name, column_definitions)
        
        # Read the CSV file into a pandas DataFrame, specifying encoding
        df = pd.read_csv(file_path, encoding='latin1')

        # Validate that all required columns are in the CSV
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            print(f"Error: The CSV file is missing the following columns: {missing_cols}")
            return
        
        # Replace NaN values with None so pymysql can handle them
        df = df.replace({np.nan: None})

        # Prepare for data insertion
        columns_sql = ", ".join([f"`{col}`" for col in required_columns])
        placeholders = ", ".join(["%s"] * len(required_columns))
        sql = f"INSERT INTO `{table_name}` ({columns_sql}) VALUES ({placeholders})"
        
        rows_inserted = 0
        for index, row in df.iterrows():
            values = tuple(row[col] for col in required_columns)
            cursor.execute(sql, values)
            rows_inserted += 1
        
        connection.commit()
        print(f"Successfully inserted {rows_inserted} rows into `{table_name}`.")

    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
        if connection:
            connection.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if connection and connection.open:
            connection.close()
            print("Database connection closed.")

# ==============================================================================
# Main Execution Block
# ==============================================================================
if __name__ == '__main__':
    # List of required columns based on your request
    required_columns_list = [
        'Code', 'Branch', 'Year', 'Risk_ID', 'Finding_ID', 'Status',
        'Date_Updated', 'Audit_Remarks', 'Verified_By'
    ]

    # Prompt the user for the file path
    csv_path = input("Enter the full path of the CSV file to upload: ")
    
    upload_data_from_csv(csv_path, 'finding_audit', required_columns_list)
