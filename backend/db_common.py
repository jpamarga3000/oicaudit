# audit_tool/backend/db_common.py (Revised for SQLAlchemy integration and get_unique_aging_dates)
import pandas as pd
import os
import pymysql
from datetime import datetime, timedelta
import re # Import regex for advanced cleaning
from sqlalchemy import create_engine, text # Import create_engine and text for parameterized queries
import traceback # Import traceback for detailed error logging


# --- Base Directories and Database Configuration ---
# AGING_BASE_DIR is no longer directly used for data loading in operations_process.py
# but kept here for reference if other parts of the system still rely on it.
AGING_BASE_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\OPERATIONS\\\\AGING"
SVACC_BASE_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\OPERATIONS\\\\SVACC"
TRNM_BASE_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\OPERATIONS\\\\TRNM"
LNACC_BASE_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\OPERATIONS\\\\LNACC" # NEW: Added LNACC_BASE_DIR
GL_BASE_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\ACCOUNTING\\\\GENERAL LEDGER" # NEW: Added GL_BASE_DIR, corrected path
TRIAL_BALANCE_BASE_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\ACCOUTNING\\\\TRIAL BALANCE" # NEW: Added TRIAL_BALANCE_BASE_DIR
# Corrected path for DEPOSIT CODE.csv
DEPOSIT_CODE_HARDCODED_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\DEPOSIT CODE.csv" # Corrected xamxampp to xampp
# Path for residence_coordinates.csv
RESIDENCE_COORDINATES_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\db\\\\residence_coordinates.csv"
# Path for list_branches.csv
LIST_BRANCHES_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\db\\\\list_branches.csv"
# Path for additional_loan_policies.csv
ADDITIONAL_LOAN_POLICIES_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\db\\\\additional_loan_policies.csv"
# NEW PATH FOR LOGIN
REGISTERED_USERS_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\db\\\\registered.csv"
# NEW PATH for profile pictures. This should point to the 'images' directory
PROFILE_PICS_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\images\\\\profile" # Directory where profile pictures are stored
# NEW PATH for Login Settings
LOGIN_SETTINGS_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\db\\\\login_settings.csv"
# NEW PATH for Restructured Loans
REST_LN_CSV_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\db\\\\rest_ln.csv" # NEW: Define REST_LN_CSV_PATH here
# NEW PATH for Game Scores
GAME_SCORE_CSV_PATH = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\db\\\\game_score.csv" # NEW: Define GAME_SCORE_CSV_PATH here


# Centralized AREA_BRANCH_MAP for backend use
AREA_BRANCH_MAP = {
    'Area 1': [
        'BAUNGON', "BULUA", "CARMEN", "COGON", "EL SALVADOR",
        "ILIGAN", "TALAKAG", "YACAPIN"
    ],
    'Area 2': [
        "AGLAYAN", "DON CARLOS", "ILUSTRE", "MANOLO", "MARAMAG",
        "TORIL", "VALENCIA"
    ],
    'Area 3': [
        "AGORA", "BALINGASAG", "BUTUAN", "GINGOOG", "PUERTO",
        "TAGBILARAN", "TUBIGON", "UBAY"
    ],
    'Consolidated': [
        'CONSOLIDATED'
    ],
    'ALL_BRANCHES_LIST': [ # This list is for internal use for 'ALL' area selection, if needed.
        'AGLAYAN', 'AGORA', 'BALINGASAG', 'BAUNGON', 'BULUA', 'BUTUAN',
        'CARMEN', 'COGON', 'DON CARLOS', 'EL SALVADOR', 'GINGOOG', 'ILIGAN',
        'ILUSTRE', 'MANOLO', 'MARAMAG', 'PUERTO', 'TAGBILARAN', 'TALAKAG',
        'TORIL', 'TUBIGON', 'UBAY', 'VALENCIA', 'YACAPIN', 'CONSOLIDATED' # Include CONSOLIDATED here if it's part of a grand total 'ALL'
    ]
}


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'dc_req_db', # This is the database where 'dosri' and 'aging_report_data' tables will reside
    'charset': 'utf8mb4' # Recommended for broader character support
}

# Removed the module-level 'engine' creation.
# It will now be created and returned by get_db_connection_sqlalchemy() function.

def get_db_connection():
    """Establishes and returns a new raw pymysql database connection (for non-pandas ops)."""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        cursorclass=pymysql.cursors.DictCursor,
        charset=DB_CONFIG['charset']
    )

def get_db_connection_sqlalchemy():
    """
    Establishes and returns a SQLAlchemy engine for database operations.
    Requires pymysql to be installed (pip install pymysql).
    """
    try:
        engine_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
        )
        engine = create_engine(engine_url)
        # Test connection (optional, but good for debugging)
        with engine.connect() as connection:
            print("Server Log (db_common): SQLAlchemy engine connected successfully.")
        return engine
    except Exception as e:
        print(f"Server Log (db_common): Error creating SQLAlchemy engine: {e}")
        traceback.print_exc()
        return None

# NEW: Helper function to fetch data from MySQL using pandas and SQLAlchemy engine
# This function now calls get_db_connection_sqlalchemy internally to get the engine
def get_data_from_mysql(query, params=None):
    """
    Fetches data from MySQL using a given query and returns it as a pandas DataFrame.
    Uses SQLAlchemy engine for better compatibility with pandas.read_sql.
    Handles database connection and error logging.
    """
    engine = get_db_connection_sqlalchemy() # Get the engine here
    if engine is None:
        print("Server Log (get_data_from_mysql): Failed to get SQLAlchemy engine. Returning empty DataFrame.")
        return pd.DataFrame()

    try:
        # --- DEBUGGING: Log the exact query and parameters ---
        print(f"DEBUG DB_COMMON (get_data_from_mysql): Executing query: {query}")
        print(f"DEBUG DB_COMMON (get_data_from_mysql): With parameters: {params}")
        # --- END DEBUGGING ---

        # Use the engine directly with pandas.read_sql
        # For parameterized queries, use sqlalchemy.text() to mark the query as literal SQL
        # and pass parameters separately.
        if params is not None:
            df = pd.read_sql(text(query), engine, params=params)
        else:
            df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Database Error (get_data_from_mysql): {e}")
        traceback.print_exc() # Print full traceback for debugging
        return pd.DataFrame() # Return empty DataFrame on error


# NEW: Function to get all unique dates from aging_report_data table
def get_unique_aging_dates(selected_branches=None):
    """
    Fetches all unique dates from the 'Date' column in the 'aging_report_data' table,
    optionally filtered by selected branches.
    Returns dates as a sorted list of strings in MM/DD/YYYY format.
    """
    print(f"Server Log (db_common): Fetching unique aging dates for branches: {selected_branches}")
    query = "SELECT DISTINCT Date FROM aging_report_data"
    params = None
    
    # MODIFIED: Refined logic to correctly handle single branch, area, or consolidated selections.
    branches_to_query_db = []
    if selected_branches:
        if not isinstance(selected_branches, list):
            selected_branches = [selected_branches] # Ensure it's a list

        for branch_item in selected_branches:
            normalized_branch_item = branch_item.strip().upper() 
            if normalized_branch_item in AREA_BRANCH_MAP:
                # Extend with actual branches from that area, excluding 'CONSOLIDATED' if it's not a real branch
                branches_to_query_db.extend([b.strip().upper() for b in AREA_BRANCH_MAP[normalized_branch_item] if b != 'CONSOLIDATED'])
            else:
                # If it's a specific branch name, add it directly (normalized)
                branches_to_query_db.append(branch_item.strip().upper())
        
        branches_to_query_db = list(set(branches_to_query_db)) # Remove duplicates

        if branches_to_query_db:
            # Use named parameters for the IN clause
            query += f" WHERE Branch IN :branches"
            params = {"branches": branches_to_query_db} # Pass as a list for the :branches placeholder
            print(f"DEBUG DB_COMMON (get_unique_aging_dates): Final branches for query: {branches_to_query_db}")
        else:
            print("Server Log (db_common): No actual branches determined for the given selection.")
            return []
    else:
        # If no specific selection, fetch dates for all branches in ALL_BRANCHES_LIST
        all_branches_from_map = [b.strip().upper() for b in AREA_BRANCH_MAP['ALL_BRANCHES_LIST'] if b != 'CONSOLIDATED']
        if all_branches_from_map:
            # Use named parameters for the IN clause
            query += f" WHERE Branch IN :branches"
            params = {"branches": all_branches_from_map}
            print(f"DEBUG DB_COMMON (get_unique_aging_dates): Fetching dates for ALL branches: {all_branches_from_map}")
        else:
            print("Server Log (db_common): No branches found in AREA_BRANCH_MAP['ALL_BRANCHES_LIST'].")
            return []
    
    query += " ORDER BY Date DESC"

    df = get_data_from_mysql(query, params=params)

    # --- DEBUGGING: Check branches found in the DataFrame after query ---
    if not df.empty and 'Branch' in df.columns:
        print(f"DEBUG DB_COMMON (get_unique_aging_dates): Branches found in query result: {df['Branch'].unique().tolist()}")
    # --- END DEBUGGING ---

    if df.empty or 'Date' not in df.columns:
        print("Server Log (db_common): No unique dates found in aging_report_data or 'Date' column missing.")
        return []

    unique_dates = pd.to_datetime(df['Date'], errors='coerce').dropna().dt.strftime('%m/%d/%Y').unique().tolist()
    
    print(f"Server Log (db_common): Found {len(unique_dates)} unique dates.")
    return unique_dates


# --- NEW: Function to create all necessary tables if they don't exist ---
def create_tables():
    """
    Ensures all necessary database tables for the application exist.
    This function should be called on application startup.
    """
    engine = get_db_connection_sqlalchemy()
    if engine is None:
        print("Error: Cannot create tables, SQLAlchemy engine not available.")
        return False

    with engine.connect() as connection:
        try:
            # Table for aging_report_data (from operations_process.py)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `aging_report_data` (
                    `Branch` VARCHAR(255),
                    `Date` DATE,
                    `CID` VARCHAR(255),
                    `Name_of_Member` VARCHAR(255),
                    `Loan_Account` VARCHAR(255),
                    `Principal` DECIMAL(18,2),
                    `Balance` DECIMAL(18,2),
                    `Aging` VARCHAR(255),
                    `Disbursement_Date` DATE,
                    `Due_Date` DATE,
                    `Product` VARCHAR(255),
                    `Group` VARCHAR(255), -- Added 'Group' column
                    PRIMARY KEY (`Loan_Account`, `Date`, `Branch`) -- Composite primary key
                );
            """))
            print("Table 'aging_report_data' ensured to exist.")

            # NEW: Table for svacc_data (for SVACC data)
            # This table is now created per branch, so this generic one is not needed
            # but leaving it here if some other part of the system still relies on a consolidated svacc_data table.
            # If not, this block can be removed.
            # connection.execute(text("""
            #     CREATE TABLE IF NOT EXISTS `svacc_data` (
            #         `ACC` VARCHAR(255) PRIMARY KEY,
            #         `CID` VARCHAR(255),
            #         `TYPE` VARCHAR(255),
            #         `BAL` DECIMAL(18,2),
            #         `ACCNAME` VARCHAR(255),
            #         `DOPEN` DATE,
            #         `INTRATE` DECIMAL(5,2),
            #         `Branch` VARCHAR(255)
            #     );
            # """))
            # print("Table 'svacc_data' ensured to exist.")


            # Table for dosri (from operations_dosri.py)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `dosri` (
                    `ID` INT AUTO_INCREMENT PRIMARY KEY,
                    `CID` VARCHAR(255),
                    `BRANCH` VARCHAR(255),
                    `NAME` VARCHAR(255),
                    `TYPE` VARCHAR(255),
                    `POSITION` VARCHAR(255),
                    `RELATED_TO` VARCHAR(255),
                    `RELATIONSHIP` VARCHAR(255)
                );
            """))
            print("Table 'dosri' ensured to exist.")

            # Table for deposit_maturity_requirements (from operations_dl.py)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `deposit_maturity_requirements` (
                    `ID` INT AUTO_INCREMENT PRIMARY KEY,
                    `Branch` VARCHAR(255),
                    `Account_No` VARCHAR(255),
                    `Client_Name` VARCHAR(255),
                    `Product_Type` VARCHAR(255),
                    `Amount` DECIMAL(18,2),
                    `Date_Opened` DATE,
                    `Maturity_Date` DATE,
                    `Interest_Rate` DECIMAL(5,2),
                    `Term` VARCHAR(255)
                );
            """))
            print("Table 'deposit_maturity_requirements' ensured to exist.")

            # Table for deposit_interest_rates (from operations_dl.py)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `deposit_interest_rates` (
                    `ID` INT AUTO_INCREMENT PRIMARY KEY,
                    `Product_Type` VARCHAR(255),
                    `Interest_Rate` DECIMAL(5,2),
                    `Effective_Date` DATE
                );
            """))
            print("Table 'deposit_interest_rates' ensured to exist.")

            # Table for former_employees (from operations_form_emp.py)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `former_employees` (
                    `ID` INT AUTO_INCREMENT PRIMARY KEY,
                    `BRANCH` VARCHAR(255),
                    `NAME` VARCHAR(255),
                    `CID` VARCHAR(255),
                    `DATE_RESIGNED` DATE,
                    `STATUS` VARCHAR(255)
                );
            """))
            print("Table 'former_employees' ensured to exist.")

            # Table for game_score (from game_leaderboard_process.py)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `game_score` (
                    `ID` INT AUTO_INCREMENT PRIMARY KEY,
                    `NAME` VARCHAR(255),
                    `SCORE` INT,
                    `TIMESTAMP` DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("Table 'game_score' ensured to exist.")

            # Table for registered users (from auth_routes.py, etc.)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `registered_users` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `First Name` VARCHAR(255),
                    `Last Name` VARCHAR(255),
                    `Contact Number` VARCHAR(20),
                    `Birthdate` DATE,
                    `Email` VARCHAR(255) UNIQUE,
                    `Username` VARCHAR(255) UNIQUE,
                    `Password` VARCHAR(255),
                    `Approved` BOOLEAN DEFAULT FALSE,
                    `Access Code` VARCHAR(255),
                    `Branch` VARCHAR(255),
                    `ProfilePicture` VARCHAR(255),
                    `Biometric_ID` VARCHAR(255),
                    `Biometric_PubKey` TEXT
                );
            """))
            print("Table 'registered_users' ensured to exist.")

            # Table for login_settings (from admin_set_routes.py)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `login_settings` (
                    `biometric_login_enabled` BOOLEAN DEFAULT TRUE,
                    `otp_verification_enabled` BOOLEAN DEFAULT TRUE
                );
            """))
            print("Table 'login_settings' ensured to exist.")
            
            # Check if login_settings table is empty, if so, insert default values
            result = connection.execute(text("SELECT COUNT(*) FROM `login_settings`;")).scalar()
            if result == 0:
                connection.execute(text("""
                    INSERT INTO `login_settings` (biometric_login_enabled, otp_verification_enabled)
                    VALUES (TRUE, TRUE);
                """))
                connection.commit() # Commit immediately after inserting default settings
                print("Default login_settings inserted.")

            # NEW: Table for dc_req (Deposit Counterpart Requirements)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `dc_req` (
                    `id` VARCHAR(255) PRIMARY KEY,
                    `product` VARCHAR(255) NOT NULL,
                    `condition` VARCHAR(255) NOT NULL,
                    `deposit_counterpart_json` TEXT
                );
            """))
            print("Table 'dc_req' ensured to exist.")
            
            # NEW: Table for finding_detail
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `finding_detail` (
                    `Finding_ID` VARCHAR(255) PRIMARY KEY,
                    `Year_Audited` VARCHAR(255),
                    `Branch` VARCHAR(255),
                    `Area` VARCHAR(255),
                    `Area_Audited` VARCHAR(255),
                    `Risk_No` VARCHAR(255),
                    `Risk_Event` VARCHAR(255),
                    `Risk_Level` VARCHAR(255)
                );
            """))
            print("Table 'finding_detail' ensured to exist.")
            
            # NEW: Table for finding_report
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `finding_report` (
                    `Finding_ID` VARCHAR(255) PRIMARY KEY,
                    `Year_Audited` VARCHAR(255),
                    `Branch` VARCHAR(255),
                    `Area` VARCHAR(255),
                    `Area_Audited` VARCHAR(255),
                    `Risk_No` VARCHAR(255),
                    `Risk_Event` VARCHAR(255),
                    `Risk_Level` VARCHAR(255)
                );
            """))
            print("Table 'finding_report' ensured to exist.")

            connection.commit() # Commit all DDL operations
            return True
        except Exception as e:
            print(f"Error during table creation in create_tables(): {e}")
            traceback.print_exc()
            connection.rollback() # Rollback in case of error
            return False

# --- NEW: CSV Helper Functions (retained for other parts of the system) ---
# (These functions are for CSV interaction, not direct DB table creation/interaction)

def read_csv_to_dataframe(file_path, encoding='utf-8', dtype=None):
    """
    Reads a CSV file into a pandas DataFrame.
    Handles FileNotFoundError and other potential pandas errors.
    If the file does not exist, it attempts to create an empty one with default headers.
    """
    try:
        if not os.path.exists(file_path):
            # Ensure the directory for the CSV file exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            filename = os.path.basename(file_path)
            default_headers = {
                'list_dosri.csv': ['ID', 'CID', 'BRANCH', 'NAME', 'TYPE', 'POSITION', 'RELATED_TO', 'RELATIONSHIP'],
                'list_former_employee.csv': ['ID', 'BRANCH', 'NAME', 'CID', 'DATE_RESIGNED', 'STATUS'],
                'registered.csv': [
                    'First Name', 'Last Name', 'Contact Number', 'Birthdate', 'Email',
                    'Username', 'Password', 'Approved', 'Access Code', 'Branch', 'ProfilePicture', 'Biometric_ID', 'Biometric_PubKey'
                ],
                'residence_coordinates.csv': ['id', 'province_city', 'city_mun_brgy', 'latitude', 'longitude'],
                'list_branches.csv': ['NO.', 'BRANCH', 'LATITUDE', 'LONGITUDE'],
                'additional_loan_policies.csv': ['ID', 'CATEGORY', 'FIELD', 'RULES'],
                'login_settings.csv': ['biometric_login_enabled', 'otp_verification_enabled'],
                'rest_ln.csv': ['BRANCH', 'CID', 'NAME', 'ACCOUNT', 'TYPE'], # Default headers for rest_ln.csv
                'game_score.csv': ['NAME', 'SCORE'] # Default headers for game_score.csv
            }
            if filename in default_headers:
                print(f"Creating empty {filename} with default headers at {file_path}")
                # For login_settings, initialize with 'True' for both by default
                if filename == 'login_settings.csv':
                    initial_data = pd.DataFrame([{'biometric_login_enabled': True, 'otp_verification_enabled': True}])
                    initial_data.to_csv(file_path, index=False, encoding=encoding)
                    return initial_data
                else:
                    # Create an empty DataFrame with specified columns
                    empty_df = pd.DataFrame(columns=default_headers[filename])
                    empty_df.to_csv(file_path, index=False, encoding=encoding)
                    return empty_df # Return empty DF immediately
            else:
                print(f"Error: CSV file not found at {file_path} and no default headers defined. Returning empty DataFrame.") # More specific error for unknown files
                return pd.DataFrame() # Return empty DataFrame if file doesn't exist for unknown files
        
        # Try reading with utf-8 first, then fall back to latin1
        try:
            df = pd.read_csv(file_path, encoding=encoding, dtype=dtype) # Pass dtype to read_csv
        except UnicodeDecodeError:
            print(f"UnicodeDecodeError with {encoding} for {file_path}. Trying 'latin1'.")
            df = pd.read_csv(file_path, encoding='latin1', dtype=dtype) # Pass dtype to read_csv
        return df
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        return pd.DataFrame()

def write_dataframe_to_csv(dataframe, file_path, encoding='utf-8'):
    """
    Writes a pandas DataFrame to a CSV file.
    Ensures the directory exists.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        dataframe.to_csv(file_path, index=False, encoding=encoding) # Use encoding
        print(f"DataFrame successfully written to {file_path}")
        return True
    except Exception as e:
        print(f"Error writing DataFrame to CSV file {file_path}: {e}")
        return False

# NEW: Function to update user profile in registered.csv
def update_user_profile_in_csv(username, updated_data):
    """
    Updates a user's profile data in registered.csv based on their username.
    Args:
        username (str): The username of the user to update.
        updated_data (dict): A dictionary of fields to update (e.g., {'First Name': 'NewName', 'Email': 'new@example.com'}).
                             Keys should match CSV headers.
    Returns:
        tuple: (bool success, str message)
    """
    try:
        df = read_csv_to_dataframe(REGISTERED_USERS_PATH)
        if df.empty or 'Username' not in df.columns:
            print(f"DEBUG DB_COMMON: registered.csv is empty or missing 'Username' column.")
            return False, "Registered users file is empty or missing 'Username' column."

        # Find the row corresponding to the username
        user_row_index = df[df['Username'] == username].index

        if user_row_index.empty:
            print(f"DEBUG DB_COMMON: User '{username}' not found in registered.csv for update.")
            return False, f"User '{username}' not found."

        # Update fields based on updated_data
        for key, value in updated_data.items():
            # Ensure the column exists in the DataFrame before attempting to update
            if key in df.columns:
                df.loc[user_row_index, key] = value
                print(f"DEBUG DB_COMMON: Updating user '{username}' column '{key}' to '{value}'.")
            else:
                print(f"DEBUG DB_COMMON: Adding/Updating user '{username}' new column '{key}' to '{value}'.")
                df.loc[user_row_index, key] = value # This will add the column if it doesn't exist
        
        # Ensure 'ProfilePicture' and 'Biometric_ID' columns exist before saving
        if 'ProfilePicture' not in df.columns:
            df['ProfilePicture'] = None
        if 'Biometric_ID' not in df.columns:
            df['Biometric_ID'] = None
        if 'Biometric_PubKey' not in df.columns: # NEW: Ensure Biometric_PubKey column exists
            df['Biometric_PubKey'] = None

        if write_dataframe_to_csv(df, REGISTERED_USERS_PATH):
            print(f"DEBUG DB_COMMON: Profile for '{username}' successfully written to registered.csv.")
            return True, "Profile updated successfully."
        else:
            print(f"DEBUG DB_COMMON: Failed to write updated profile for '{username}' to registered.csv.")
            return False, "Failed to write updated profile to CSV."

    except Exception as e:
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        print(f"DEBUG DB_COMMON: Exception during profile update in CSV: {e}")
        return False, f"An error occurred during profile update: {e}"

# NEW: Function to get profile picture path for a user
def get_profile_picture_path(username):
    """
    Retrieves the profile picture filename for a given username from registered.csv.
    Returns the filename if found and the file exists in the PROFILE_PICS_DIR, otherwise None.
    """
    try:
        df = read_csv_to_dataframe(REGISTERED_USERS_PATH)
        if df.empty or 'Username' not in df.columns:
            print(f"DEBUG DB_COMMON: registered.csv empty or missing 'Username' for get_profile_picture_path.")
            return None # No data, or missing columns

        # Ensure 'ProfilePicture' column exists, if not, add it for consistency
        if 'ProfilePicture' not in df.columns:
            df['ProfilePicture'] = None # Add the column with default None
            print(f"DEBUG DB_COMMON: 'ProfilePicture' column added to DataFrame (was missing).")
            # Attempt to save the updated DataFrame to ensure the CSV file has the new column
            if not write_dataframe_to_csv(df, REGISTERED_USERS_PATH):
                print(f"DEBUG DB_COMMON: Failed to add 'ProfilePicture' column to {REGISTERED_USERS_PATH}.")
                return None

        user_row = df[df['Username'] == username]
        if not user_row.empty:
            profile_pic_filename = user_row['ProfilePicture'].iloc[0]
            print(f"DEBUG DB_COMMON: For user '{username}', 'ProfilePicture' in CSV is: '{profile_pic_filename}'")
            
            if pd.isna(profile_pic_filename) or not profile_pic_filename:
                print(f"DEBUG DB_COMMON: No profile picture filename stored for '{username}' in CSV.")
                return None # No filename stored in CSV

            # Construct the full path and check if the file exists on disk
            full_path = os.path.join(PROFILE_PICS_DIR, profile_pic_filename)
            if os.path.exists(full_path):
                print(f"DEBUG DB_COMMON: Profile picture file exists at '{full_path}'.")
                return profile_pic_filename
            else:
                print(f"DEBUG DB_COMMON: Profile picture file DOES NOT exist at '{full_path}'.")
                return None # File not found on disk
        else:
            print(f"DEBUG DB_COMMON: User '{username}' not found in registered.csv for get_profile_picture_path.")
        return None # User not found or file not found on disk
    except Exception as e:
        print(f"DEBUG DB_COMMON: Exception during get_profile_picture_path: {e}")
        import traceback
        traceback.print_exc()
        return None

# NEW: Function to get biometric ID for a user
def get_biometric_id(username):
    """
    Retrieves the Biometric_ID for a given username from registered.csv.
    Returns the Biometric_ID string if found, otherwise None.
    """
    try:
        df = read_csv_to_dataframe(REGISTERED_USERS_PATH)
        if df.empty or 'Username' not in df.columns:
            print(f"DEBUG DB_COMMON: registered.csv empty or missing 'Username' for get_biometric_id.")
            return None

        if 'Biometric_ID' not in df.columns:
            # If 'Biometric_ID' is missing, add it and save the CSV to ensure the header exists
            df['Biometric_ID'] = None
            print(f"DEBUG DB_COMMON: 'Biometric_ID' column added to DataFrame (was missing).")
            # Attempt to save the updated DataFrame to ensure the CSV file has the new column
            if not write_dataframe_to_csv(df, REGISTERED_USERS_PATH):
                print(f"DEBUG DB_COMMON: Failed to add 'Biometric_ID' column to {REGISTERED_USERS_PATH}.")
                return None

        user_row = df[df['Username'] == username]
        if not user_row.empty:
            biometric_id = user_row['Biometric_ID'].iloc[0]
            if pd.isna(biometric_id) or not str(biometric_id).strip():
                print(f"DEBUG DB_COMMON: No Biometric_ID stored for '{username}'.")
                return None
            print(f"DEBUG DB_COMMON: Biometric_ID found for '{username}': {biometric_id}")
            return str(biometric_id).strip()
        else:
            print(f"DEBUG DB_COMMON: User '{username}' not found in registered.csv for get_biometric_id.")
        return None
    except Exception as e:
        print(f"DEBUG DB_COMMON: Exception during get_biometric_id: {e}")
        import traceback
        traceback.print_exc()
        return None

# NEW: Function to get user's first name by username
def get_user_first_name(username):
    """
    Retrieves the 'First Name' for a given username from registered.csv.
    Returns the first name string if found, otherwise None.
    """
    try:
        df = read_csv_to_dataframe(REGISTERED_USERS_PATH)
        if df.empty or 'Username' not in df.columns:
            print(f"DEBUG DB_COMMON: registered.csv empty or missing 'Username'/'First Name' for get_user_first_name.")
            return None
        
        user_row = df[df['Username'] == username]
        if not user_row.empty:
            first_name = user_row['First Name'].iloc[0]
            if pd.isna(first_name) or not str(first_name).strip():
                print(f"DEBUG DB_COMMON: No First Name stored for '{username}'.")
                return None
            return str(first_name).strip()
        else:
            print(f"DEBUG DB_COMMON: User '{username}' not found in registered.csv for get_user_first_name.")
        return None
    except Exception as e:
        print(f"DEBUG DB_COMMON: Exception during get_user_first_name: {e}")
        import traceback
        traceback.print_exc()
        return None


# NEW: Functions for Login Settings
def read_login_settings():
    """
    Reads the login settings from login_settings.csv.
    Initializes with default values (True for both) if the file doesn't exist.
    Returns a dictionary {'biometric_login_enabled': bool, 'otp_verification_enabled': bool}.
    """
    try:
        df = read_csv_to_dataframe(LOGIN_SETTINGS_PATH)
        if df.empty:
            # This case should ideally be handled by read_csv_to_dataframe creating the file,
            # but as a fallback, ensure defaults are returned.
            return {'biometric_login_enabled': True, 'otp_verification_enabled': True}
        
        # Ensure column names are stripped
        df.columns = df.columns.str.strip()

        # Get the first (and only) row of settings
        settings = df.iloc[0]
        
        biometric_enabled = settings.get('biometric_login_enabled', True)
        otp_enabled = settings.get('otp_verification_enabled', True)

        # Convert to boolean explicitly (CSV might store "True"/"False" strings or 1/0)
        biometric_enabled = str(biometric_enabled).lower() == 'true' or biometric_enabled == 1
        otp_enabled = str(otp_enabled).lower() == 'true' or otp_enabled == 1

        print(f"DEBUG DB_COMMON: Read login settings - Biometric: {biometric_enabled}, OTP: {otp_enabled}")
        return {
            'biometric_login_enabled': biometric_enabled,
            'otp_verification_enabled': otp_enabled
        }
    except Exception as e:
        print(f"Error reading login settings: {e}. Returning default settings.")
        import traceback
        traceback.print_exc()
        return {'biometric_login_enabled': True, 'otp_verification_enabled': True}

def write_login_settings(settings_data):
    """
    Writes/updates the login settings to login_settings.csv.
    Args:
        settings_data (dict): A dictionary with 'biometric_login_enabled' and 'otp_verification_enabled' boolean values.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create a DataFrame from the settings data
        df = pd.DataFrame([settings_data])
        
        if write_dataframe_to_csv(df, LOGIN_SETTINGS_PATH):
            print(f"DEBUG DB_COMMON: Login settings successfully written to {LOGIN_SETTINGS_PATH}")
            return True
        else:
            print(f"DEBUG DB_COMMON: Failed to write login settings to {LOGIN_SETTINGS_PATH}")
            return False
    except Exception as e:
        print(f"Error writing login settings: {e}")
        import traceback
        traceback.print_exc()
        return False


# --- Common Helper Functions for Data Processing ---

def format_currency_py(value):
    """
    Formats a numeric value to a string with comma separators,
    two decimal places, WITHOUT currency sign. Returns "0.00" if value is NaN or None.
    """
    if pd.isna(value) or value is None:
        return "0.00"

    num_val = float(value)
    if num_val < 0:
        return "({:,.2f})".format(abs(num_val))
    else:
        return "{:,.2f}".format(num_val)

def format_signed_currency_py(value):
    """
    Formats a numeric value to a string with comma separators,
    two decimal places, and parentheses for negative numbers, WITHOUT currency sign.
    Returns "0.00" if value is NaN or None.
    """
    if pd.isna(value) or value is None:
        return "0.00"
    num_val = float(value)
    if num_val < 0:
        return "({:,.2f})".format(abs(num_val))
    else:
        return "{:,.2f}".format(num_val)

def normalize_cid_py(cid_str):
    """
    Normalizes CID strings: '0001', '001', '1' all become '1'.
    Handles cases where CID might be NaN or other non-numeric strings.
    """
    if pd.isna(cid_str) or str(cid_str).strip() == '':
        return ''
    s_cid = str(cid_str).strip()
    if s_cid.isdigit():
        return str(int(s_cid))
    return s_cid

def _clean_field(value):
    """Converts to string, strips, and normalizes common numerical representations.
    Returns an empty string '' for effectively blank values after cleaning.
    """
    if value is None:
        return ''
    s_val = str(value).strip()

    if not s_val:
        return ''

    try:
        if s_val.replace('.', '', 1).isdigit(): # Allows for decimals like '1.0'
            return str(int(float(s_val)))
    except ValueError:
        pass

    return s_val

def parse_currency_to_number_py(currency_string):
    """
    Parses a currency string (e.g., "$1,234.56" or "(1,234.56)") into a float.
    Handles parentheses for negative numbers and removes commas.
    """
    if not isinstance(currency_string, str):
        return float(currency_string)

    cleaned_string = currency_string.replace('₱', '').replace('$', '').replace(',', '').strip()

    if cleaned_string.startswith('(') and cleaned_string.endswith(')'):
        try:
            return -float(cleaned_string[1:-1])
        except ValueError:
            return 0.0
    else:
        try:
            return float(cleaned_string)
        except ValueError:
            return 0.0

def _clean_numeric_string_for_conversion(s):
    """
    Aggressively cleans a string to prepare it for numeric conversion.
    Removes commas, currency symbols, and trims whitespace.
    Handles common representations of numbers.
    """
    if pd.isna(s):
        return ''
    s = str(s).strip()
    s = s.replace(',', '') # Remove commas
    s = s.replace('₱', '') # Remove common currency symbols if they somehow got there
    s = s.replace('$', '')
    s = s.replace('(', '-') # Convert parentheses for negatives
    s = s.replace(')', '')
    # Ensure it's not just whitespace
    if not s:
        return ''
    return s

def get_latest_data_for_month(df, date_col, target_date, id_col):
    """
    Filters DataFrame for records on or before the target date,
    and returns the latest record for each unique identifier.
    Assumes `date_col` is already in datetime format.

    Args:
        df (pd.DataFrame): The input DataFrame.
        date_col (str): The name of the date column (must be datetime type).
        target_date (datetime): The specific date (day, month, year) to filter by.
        id_col (str): The column used to identify unique records (e.g., 'LOAN ACCT.', 'ACC').

    Returns:
        pd.DataFrame: A DataFrame containing the latest record for each unique `id_col`
                      on or before the target date.
                      Returns an empty DataFrame if no data matches.
    """
    if df.empty:
        print(f"Server Log (get_latest_data_for_month): Input DataFrame is empty. Returning empty DataFrame.")
        return pd.DataFrame()

    if date_col not in df.columns:
        print(f"Server Log (get_latest_data_for_month): Date column '{date_col}' not found in DataFrame. Returning empty DataFrame.")
        return pd.DataFrame()

    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        print(f"Server Log (get_latest_data_for_month): Date column '{date_col}' is not datetime type. Attempting conversion.")
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df.dropna(subset=[date_col], inplace=True)
        print(f"Server Log (get_latest_data_for_month): After conversion attempt, '{date_col}' dtypes: {df[date_col].dtype}")

    # --- ADDED DEBUG: Inspect unique dates and target date for comparison ---
    print(f"DEBUG (get_latest_data_for_month): Unique dates in '{date_col}' before filtering (sample): {df[date_col].dt.date.unique()[:5].tolist()}...")
    print(f"DEBUG (get_latest_data_for_month): Target date for filtering: {target_date.date()} (type: {type(target_date.date())})")
    # --- END ADDED DEBUG ---

    # Filter for records on or before the target_date
    # Removed the month and year restriction to get the absolute latest record up to the target date.
    df_filtered_by_date = df[
        (df[date_col].dt.date <= target_date.date())
    ].copy()
    print(f"DEBUG (get_latest_data_for_month): After filtering <= target_date ({target_date.date()}), df_filtered_by_date shape: {df_filtered_by_date.shape}")

    if df_filtered_by_date.empty:
        print(f"Server Log (get_latest_data_for_month): No data found on or before target date {target_date.date()}. Returning empty DataFrame.")
        return pd.DataFrame()

    # Sort by date_col (ascending) to ensure 'last' duplicate is the latest for that ID on or before the target date
    df_filtered_by_date.sort_values(by=date_col, ascending=True, inplace=True)
    latest_data = df_filtered_by_date.drop_duplicates(subset=[id_col], keep='last').copy()

    print(f"Server Log (get_latest_data_for_month): Final latest_data shape: {latest_data.shape}")
    return latest_data

def get_tb_latest_date(branch_name):
    """
    Gets the latest date from Trial Balance CSV/XLSX filenames for a given branch.
    Looks inside the TRIAL_BALANCE_BASE_DIR, then in a subfolder matching the branch name,
    and finds the latest file based on MM-DD-YYYY.csv or MM-DD-YYYY.xlsx format.
    Example: C:\\xampp\\\\htdocs\\\\audit_tool\\\\ACCOUTNING\\\\TRIAL BALANCE\\\\BRANCH_NAME\\\\MM-DD-YYYY.csv
    """
    # Normalize branch name for folder lookup (replace spaces with underscores)
    normalized_branch_name_for_folder = branch_name.replace(' ', '_').upper()
    branch_path = os.path.join(TRIAL_BALANCE_BASE_DIR, normalized_branch_name_for_folder)
    
    if not os.path.isdir(branch_path):
        print(f"DEBUG DB_COMMON (get_tb_latest_date): Branch path not found: {branch_path}")
        return "-"

    all_dates = []
    # Regex to capture MM-DD-YYYY date from the filename, allowing both .csv and .xlsx
    date_pattern = re.compile(r'^(\d{2}-\d{2}-\d{4})\.(?:csv|xlsx)$', re.IGNORECASE)

    for file in os.listdir(branch_path):
        # Removed the specific .csv check, now handled by regex
        match = date_pattern.match(file)
        if match:
            try:
                date_str = match.group(1)
                # Convert MM-DD-YYYY to datetime object
                all_dates.append(datetime.strptime(date_str, "%m-%d-%Y"))
            except ValueError as ve:
                print(f"Warning: Could not parse date '{date_str}' from TB filename '{file}': {ve}")
                continue
    
    if all_dates:
        max_date = max(all_dates)
        formatted_date = max_date.strftime("%m/%d/%Y") # Format to MM/DD/YYYY
        print(f"DEBUG DB_COMMON (get_tb_latest_date): Latest date for {branch_name}: {formatted_date}")
        return formatted_date
    else:
        print(f"DEBUG DB_COMMON (get_tb_latest_date): No TB files found for branch: {branch_name}")
        return "-"

