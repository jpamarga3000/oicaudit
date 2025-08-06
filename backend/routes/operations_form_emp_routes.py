from flask import Blueprint, request, jsonify
import traceback
import tempfile
import shutil
import os # Import the os module

# Import processing functions
from operations_dosri import ( # Note: These are still in operations_dosri.py as per original app.py
    process_form_emp_loan_balances,
    process_form_emp_deposit_liabilities
)
from operations_form_emp import (
    get_form_emp_data, add_form_emp_entry, update_form_emp_entry, delete_form_emp_entry,
    upload_form_emp_csv_to_db
)

operations_form_emp_bp = Blueprint('operations_form_emp', __name__)

@operations_form_emp_bp.route('/api/form_emp', methods=['GET'])
def api_get_form_emp():
    """Fetches all Former Employee records from CSV, with optional search and status filters."""
    search_term = request.args.get('search_term', '')
    status_filter = request.args.get('type_filter', '') # Corrected from type_filter to status_filter
    try:
        form_emp_list = get_form_emp_data(search_term=search_term, type_filter=status_filter) # Pass filters
        # Ensure column names match frontend expectations
        formatted_list = []
        for item in form_emp_list:
            formatted_item = {
                "id": item.get("ID"), # Use uppercase 'ID' from CSV
                "BRANCH": item.get("BRANCH"),
                "NAME": item.get("NAME"),
                "CID": item.get("CID"),
                "DATE RESIGNED": item.get("DATE_RESIGNED"), # Map internal to frontend key
                "STATUS": item.get("STATUS")
            }
            formatted_list.append(formatted_item)
        return jsonify({"form_emp_list": formatted_list}), 200
    except Exception as e:
        print(f"Error fetching Former Employee list from CSV: {e}")
        return jsonify({"error": f"Failed to retrieve Former Employee list: {str(e)}"}), 500

@operations_form_emp_bp.route('/api/form_emp/<int:emp_id>', methods=['GET'])
def api_get_single_form_emp(emp_id):
    """Fetches a single Former Employee record by ID from CSV."""
    try:
        form_emp_record = get_form_emp_data(entry_id=emp_id)
        if form_emp_record:
            formatted_record = {
                "id": form_emp_record.get("ID"),
                "BRANCH": form_emp_record.get("BRANCH"),
                "NAME": form_emp_record.get("NAME"),
                "CID": form_emp_record.get("CID"),
                "DATE RESIGNED": form_emp_record.get("DATE_RESIGNED"),
                "STATUS": form_emp_record.get("STATUS")
            }
            return jsonify({"form_emp_record": formatted_record}), 200
        else:
            return jsonify({"message": "Former Employee record not found."}), 404
    except Exception as e:
        print(f"Error fetching Former Employee record {emp_id} from CSV: {e}")
        return jsonify({"error": f"Failed to retrieve Former Employee record: {str(e)}"}), 500

@operations_form_emp_bp.route('/api/form_emp', methods=['POST'])
def api_add_form_emp():
    """Adds a new Former Employee record to CSV."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data provided."}), 400

    processed_data = {
        "branch": data.get("BRANCH"),
        "name": data.get("NAME"),
        "cid": data.get("CID"),
        "date_resigned": data.get("DATE RESIGNED"), # Use the frontend key
        "status": data.get("STATUS")
    }

    if not processed_data.get('name') or not processed_data.get('branch'):
        return jsonify({"error": "Name and Branch are required fields."}), 400
    try:
        add_form_emp_entry(processed_data) # Pass the dictionary directly
        return jsonify({"message": "Former Employee record added successfully."}), 201
    except Exception as e:
        print(f"Error adding Former Employee record to CSV: {e}")
        return jsonify({"error": f"Failed to add Former Employee record: {str(e)}"}), 500

@operations_form_emp_bp.route('/api/form_emp/<int:emp_id>', methods=['PUT'])
def api_update_form_emp(emp_id):
    """Updates an existing Former Employee record in CSV."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data provided."}), 400

    processed_data = {
        "branch": data.get("BRANCH"),
        "name": data.get("NAME"),
        "cid": data.get("CID"),
        "date_resigned": data.get("DATE RESIGNED"), # Use the frontend key
        "status": data.get("STATUS")
    }

    if not processed_data.get('name') or not processed_data.get('branch'):
        return jsonify({"error": "Name and Branch are required fields."}), 400
    try:
        update_form_emp_entry(emp_id, processed_data) # Pass ID and dictionary
        return jsonify({"message": f"Former Employee record {emp_id} updated successfully."}), 200
    except Exception as e:
        print(f"Error updating Former Employee record {emp_id} in CSV: {e}")
        return jsonify({"error": f"Failed to update Former Employee record: {str(e)}"}), 500

@operations_form_emp_bp.route('/api/form_emp/<int:emp_id>', methods=['DELETE'])
def api_delete_form_emp(emp_id):
    """Deletes a Former Employee record from CSV."""
    try:
        delete_form_emp_entry(emp_id) # Pass ID
        return jsonify({"message": f"Former Employee record {emp_id} deleted successfully."}), 200
    except Exception as e:
        print(f"Error deleting Former Employee record {emp_id} from CSV: {e}")
        return jsonify({"error": f"Failed to delete Former Employee record: {str(e)}"}), 500

@operations_form_emp_bp.route('/api/form_emp/upload_csv', methods=['POST'])
def api_upload_form_emp_csv():
    """Handles CSV file upload for Former Employee data, saving to CSV."""
    if 'csv_file' not in request.files:
        return jsonify({"error": "No CSV file part in the request."}), 400

    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    upload_option = request.form.get('upload_option', 'override')

    if file and file.filename.endswith('.csv'):
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, file.filename)
        try:
            file.save(filepath)
            upload_form_emp_csv_to_db(filepath, upload_option=upload_option)
            return jsonify({"message": f"Former Employee data uploaded successfully using '{upload_option}' option."}), 200
        except Exception as e:
            print(f"Error during Former Employee CSV upload: {e}")
            return jsonify({"error": f"Failed to upload CSV: {str(e)}"}), 500
        finally:
            shutil.rmtree(temp_dir)
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

@operations_form_emp_bp.route('/api/form_emp_list', methods=['GET'])
def api_get_form_emp_list_summary():
    """
    API endpoint to retrieve the list of Former Employee members for summary reports.
    Fetches data from the CSV using get_form_emp_data and returns it formatted for the frontend.
    """
    try:
        # Fetch all Former Employee data (now from CSV)
        form_emp_list = get_form_emp_data()

        # Format the data to match the expected structure for frontend summary requests
        # The frontend operations_dosri.js expects 'branch', 'cid', and 'name' keys for members.
        # Ensure that 'BRANCH', 'CID', and 'NAME' from your form_emp table are mapped correctly.
        formatted_form_emp_members = []
        for member in form_emp_list:
            formatted_form_emp_members.append({
                "branch": member.get("BRANCH"), # Assuming 'BRANCH' is the column name in your CSV
                "cid": member.get("CID"),      # Assuming 'CID' is the column name in your CSV
                "name": member.get("NAME")      # Assuming 'NAME' is the column name in your CSV
            })

        return jsonify({"form_emp_list": formatted_form_emp_members}), 200
    except Exception as e:
        print(f"Error fetching Former Employees list for summary: {e}")
        return jsonify({"error": f"Failed to retrieve Former Employees list for summary: {str(e)}"}), 500


@operations_form_emp_bp.route('/api/form_emp/loan_balances', methods=['POST'])
def api_process_form_emp_loan_balances():
    """
    API endpoint to process Former Employee loan balances.
    Calls the backend processing logic from operations_dosri.py.
    Now accepts 'form_emp_members' and 'report_date' from the request JSON.
    """
    data = request.get_json()
    form_emp_members = data.get('form_emp_members', [])
    report_date = data.get('report_date') # Get the report_date

    return process_form_emp_loan_balances(form_emp_members=form_emp_members, report_date=report_date)

@operations_form_emp_bp.route('/api/form_emp/deposit_liabilities', methods=['POST'])
def api_process_form_emp_deposit_liabilities():
    """
    API endpoint to process Former Employee deposit liabilities.
    Calls the backend processing logic from operations_dosri.py.
    Now accepts 'form_emp_members' and 'report_date' from the request JSON.
    """
    data = request.get_json()
    form_emp_members = data.get('form_emp_members', [])
    report_date = data.get('report_date') # Get the report_date

    return process_form_emp_deposit_liabilities(form_emp_members=form_emp_members, report_date=report_date)
