from flask import Blueprint, request, jsonify
import pandas as pd
import traceback

# Import necessary functions/constants from db_common.py
# Assuming db_common.py is in the 'backend' directory, so use absolute import
from backend.db_common import read_csv_to_dataframe, write_dataframe_to_csv, RESIDENCE_COORDINATES_PATH, LIST_BRANCHES_PATH, ADDITIONAL_LOAN_POLICIES_PATH

reference_data_bp = Blueprint('reference_data', __name__)

@reference_data_bp.route('/get_residence_coordinates', methods=['GET'])
def get_residence_coordinates():
    """
    Reads the residence_coordinates.csv file and returns its content as JSON.
    """
    try:
        df = read_csv_to_dataframe(RESIDENCE_COORDINATES_PATH)
        # Ensure 'id' column exists and is unique, if not, generate simple IDs
        if 'id' not in df.columns or df['id'].duplicated().any():
            df['id'] = range(1, len(df) + 1)
        # Convert DataFrame to a list of dictionaries (JSON format)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        print(f"Error fetching residence coordinates: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Failed to fetch residence coordinates.", "details": str(e)}), 500

@reference_data_bp.route('/save_residence_coordinates', methods=['POST'])
def save_residence_coordinates():
    """
    Receives JSON data and saves it back to residence_coordinates.csv.
    Expects a list of dictionaries.
    """
    try:
        data = request.json
        if not isinstance(data, list):
            return jsonify({"error": "Invalid data format. Expected a list of records."}), 400

        # Convert list of dicts to DataFrame
        df = pd.DataFrame(data)

        # Basic validation: ensure required columns are present
        required_cols = ['id', 'province_city', 'city_mun_brgy', 'latitude', 'longitude']
        if not all(col in df.columns for col in required_cols):
            return jsonify({"error": "Missing required columns in data. Expected: id, province_city, city_mun_brgy, latitude, longitude"}), 400

        # Drop any rows that are completely empty if they somehow make it here from client side
        df.dropna(how='all', inplace=True)
        if df.empty:
            return jsonify({"message": "No data to save (received empty dataset)."}), 200

        # Ensure 'id' column is numeric and unique. If new rows don't have IDs, assign new ones.
        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        # Filter out rows with invalid IDs for now or assign them new ones
        df['id'] = df['id'].apply(lambda x: int(x) if pd.notna(x) else None)

        # For new rows (id is None or 0 or NaN after conversion), assign new unique IDs
        max_id = df['id'].max() if pd.notna(df['id'].max()) else 0
        new_id_counter = 1
        for index, row in df.iterrows():
            if pd.isna(row['id']) or row['id'] <= 0:
                df.at[index, 'id'] = int(max_id + new_id_counter)
                new_id_counter += 1

        # Ensure all IDs are unique after assignment
        if df['id'].duplicated().any():
            # If duplicates still exist (e.g., user entered same ID for new rows), reassign all IDs
            print("Warning: Duplicate 'ID' values found in Residence Coordinates. Reassigning unique sequential numbers.")
            df['id'] = range(1, len(df) + 1)

        df = df.sort_values(by='id').reset_index(drop=True)

        if write_dataframe_to_csv(df, RESIDENCE_COORDINATES_PATH):
            return jsonify({"message": "Residence coordinates saved successfully."}), 200
        else:
            return jsonify({"error": "Failed to save residence coordinates to CSV."}), 500
    except Exception as e:
        print(f"Error saving residence coordinates: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "An error occurred while saving residence coordinates.", "details": str(e)}), 500

@reference_data_bp.route('/get_branches_data', methods=['GET'])
def get_branches_data():
    """
    Reads the list_branches.csv file and returns its content as JSON.
    """
    try:
        df = read_csv_to_dataframe(LIST_BRANCHES_PATH)
        # Assuming list_branches.csv has headers: NO., BRANCH, LATITUDE, LONGITUDE
        # Convert DataFrame to a list of dictionaries (JSON format)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        print(f"Error fetching branches data: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Failed to fetch branches data.", "details": str(e)}), 500

@reference_data_bp.route('/save_branches_data', methods=['POST'])
def save_branches_data():
    """
    Receives JSON data and saves it back to list_branches.csv.
    Expects a list of dictionaries.
    """
    try:
        data = request.json
        if not isinstance(data, list):
            return jsonify({"error": "Invalid data format. Expected a list of records."}), 400

        # Convert list of dicts to DataFrame
        df = pd.DataFrame(data)

        # Basic validation: ensure required columns are present
        required_cols = ['NO.', 'BRANCH', 'LATITUDE', 'LONGITUDE']
        if not all(col in df.columns for col in required_cols):
            return jsonify({"error": "Missing required columns in data. Expected: NO., BRANCH, LATITUDE, LONGITUDE"}), 400

        # Drop any rows that are completely empty
        df.dropna(how='all', inplace=True)
        if df.empty:
            return jsonify({"message": "No data to save (received empty dataset)."}), 200

        # Ensure 'NO.' column is numeric and unique.
        # This part assumes 'NO.' is intended as a primary key or unique identifier.
        # If 'NO.' can be duplicated or is not a proper ID, adjust logic.
        df['NO.'] = pd.to_numeric(df['NO.'], errors='coerce')
        df.dropna(subset=['NO.'], inplace=True) # Drop rows where 'NO.' is not a valid number
        df['NO.'] = df['NO.'].astype(int)

        # If 'NO.' should be unique and assigned automatically for new rows
        # For simplicity, if NO. is not unique, reassign them.
        if df['NO.'].duplicated().any():
            # A more robust approach might involve checking which rows are 'new'
            # (e.g., if the frontend sends a flag) or trying to merge.
            # For this context, reassigning unique numbers if duplicates exist.
            print("Warning: Duplicate 'NO.' values detected. Reassigning unique sequential numbers.")
            df['NO.'] = range(1, len(df) + 1)

        df = df.sort_values(by='NO.').reset_index(drop=True)


        if write_dataframe_to_csv(df, LIST_BRANCHES_PATH):
            return jsonify({"message": "Branches data saved successfully."}), 200
        else:
            return jsonify({"error": "Failed to save branches data to CSV."}), 500
    except Exception as e:
        print(f"Error saving branches data: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "An error occurred while saving branches data.", "details": str(e)}), 500

@reference_data_bp.route('/get_additional_loan_policies', methods=['GET'])
def get_additional_loan_policies():
    """
    Reads the additional_loan_policies.csv file and returns its content as JSON.
    """
    try:
        df = read_csv_to_dataframe(ADDITIONAL_LOAN_POLICIES_PATH)
        # Ensure 'ID' column exists and is unique, if not, generate simple IDs
        if 'ID' not in df.columns or df['ID'].duplicated().any():
            df['ID'] = range(1, len(df) + 1)
        # Convert DataFrame to a list of dictionaries (JSON format)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        print(f"Error fetching additional loan policies: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Failed to fetch additional loan policies.", "details": str(e)}), 500

@reference_data_bp.route('/save_additional_loan_policies', methods=['POST'])
def save_additional_loan_policies():
    """
    Receives JSON data and saves it back to additional_loan_policies.csv.
    Expects a list of dictionaries.
    """
    try:
        data = request.json
        if not isinstance(data, list):
            return jsonify({"error": "Invalid data format. Expected a list of records."}), 400

        # Convert list of dicts to DataFrame
        df = pd.DataFrame(data)

        # Basic validation: ensure required columns are present
        required_cols = ['ID', 'CATEGORY', 'FIELD', 'RULES']
        if not all(col in df.columns for col in required_cols):
            return jsonify({"error": "Missing required columns in data. Expected: ID, CATEGORY, FIELD, RULES"}), 400

        # Drop any rows that are completely empty
        df.dropna(how='all', inplace=True)
        if df.empty:
            return jsonify({"message": "No data to save (received empty dataset)."}), 200

        # Ensure 'ID' column is numeric and unique.
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
        df['ID'] = df['ID'].apply(lambda x: int(x) if pd.notna(x) else None)

        # For new rows (ID is None or 0 or NaN after conversion), assign new unique IDs
        max_id = df['ID'].max() if pd.notna(df['ID'].max()) else 0
        new_id_counter = 1
        for index, row in df.iterrows():
            if pd.isna(row['ID']) or row['ID'] <= 0:
                df.at[index, 'ID'] = int(max_id + new_id_counter)
                new_id_counter += 1

        # Ensure all IDs are unique after assignment
        if df['ID'].duplicated().any():
            print("Warning: Duplicate 'ID' values detected for Additional Loan Policies. Reassigning unique sequential numbers.")
            df['ID'] = range(1, len(df) + 1)

        df = df.sort_values(by='ID').reset_index(drop=True)

        if write_dataframe_to_csv(df, ADDITIONAL_LOAN_POLICIES_PATH):
            return jsonify({"message": "Additional Loan Policies saved successfully."}), 200
        else:
            return jsonify({"error": "Failed to save additional loan policies to CSV."}), 500
    except Exception as e:
        print(f"Error saving additional loan policies: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "An error occurred while saving additional loan policies.", "details": str(e)}), 500

