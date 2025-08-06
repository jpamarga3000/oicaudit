from flask import Blueprint, request, jsonify, send_file
import traceback
import tempfile
import shutil
import os # Import the os module

# Import processing functions
from operations_dosri import (
    get_dosri_data, add_dosri_entry, update_dosri_entry, delete_dosri_entry,
    upload_dosri_csv_to_db,
    process_dosri_loan_balances, process_dosri_deposit_liabilities,
    download_dosri_excel_report
)

operations_dosri_bp = Blueprint('operations_dosri', __name__)

@operations_dosri_bp.route('/api/dosri', methods=['GET'])
def api_get_dosri():
    """Fetches all DOSRI records from CSV. Relies on 'id' for display and sub-requests."""
    search_term = request.args.get('search_term', '')
    type_filter = request.args.get('type_filter', '')
    try:
        dosri_list = get_dosri_data(search_term=search_term, type_filter=type_filter) # Pass filters
        formatted_dosri_list = []
        for item in dosri_list:
            formatted_type = item.get("TYPE")
            if formatted_type == 'Related Interest':
                # Concatenate 'TYPE' &" ("&'RELATED_TO'&" - "&'RELATIONSHIP'&")"
                related_to = item.get("RELATED_TO", "")
                relationship = item.get("RELATIONSHIP", "")
                formatted_type = f"{formatted_type} ({related_to} - {relationship})"

            formatted_item = {
                "id": item.get("ID"), # Use uppercase 'ID' from CSV
                "cid": item.get("CID"),
                "branch": item.get("BRANCH"),
                "name": item.get("NAME"),
                "type": formatted_type, # Use the potentially modified type
                "position": item.get("POSITION"),
                "related_to": item.get("RELATED_TO"),
                "relationship": item.get("RELATIONSHIP")
            }
            formatted_dosri_list.append(formatted_item)
        return jsonify({"dosri_list": formatted_dosri_list}), 200
    except Exception as e:
        print(f"Error fetching DOSRI list from CSV: {e}")
        return jsonify({"error": f"Failed to retrieve DOSRI list: {str(e)}"}), 500


@operations_dosri_bp.route('/api/dosri/<int:dosri_id>', methods=['GET'])
def api_get_single_dosri(dosri_id):
    """Fetches a single DOSRI record by ID from CSV."""
    try:
        dosri_record = get_dosri_data(entry_id=dosri_id) # Use entry_id parameter
        if dosri_record:
            formatted_record = {
                "id": dosri_record.get("ID"),
                "cid": dosri_record.get("CID"),
                "branch": dosri_record.get("BRANCH"),
                "name": dosri_record.get("NAME"),
                "type": dosri_record.get("TYPE"),
                "position": dosri_record.get("POSITION"),
                "related_to": dosri_record.get("RELATED_TO"),
                "relationship": dosri_record.get("RELATIONSHIP")
            }
            return jsonify({"dosri_record": formatted_record}), 200
        else:
            return jsonify({"message": "DOSRI record not found."}), 404
    except Exception as e:
        print(f"Error fetching DOSRI record {dosri_id} from CSV: {e}")
        return jsonify({"error": f"Failed to retrieve DOSRI record: {str(e)}"}), 500

@operations_dosri_bp.route('/api/dosri', methods=['POST'])
def api_add_dosri():
    """Adds a new DOSRI record to CSV."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data provided."}), 400

    processed_data = {
        "cid": data.get("CID"),
        "branch": data.get("BRANCH"),
        "name": data.get("NAME"),
        "type": data.get("TYPE"),
        "position": data.get("POSITION"),
        "related_to": data.get("RELATED TO"), # Frontend key name
        "relationship": data.get("RELATIONSHIP") # Frontend key name
    }

    if not processed_data.get('name') or not processed_data.get('type') or not processed_data.get('branch'):
        return jsonify({"error": "Name, Type, and Branch are required fields."}), 400
    try:
        add_dosri_entry(processed_data)
        return jsonify({"message": "DOSRI record added successfully."}), 201
    except Exception as e:
        print(f"Error adding DOSRI record to CSV: {e}")
        return jsonify({"error": f"Failed to add DOSRI record: {str(e)}"}), 500

@operations_dosri_bp.route('/api/dosri/<int:dosri_id>', methods=['PUT'])
def api_update_dosri(dosri_id):
    """Updates an existing DOSRI record in CSV."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data provided."}), 400

    processed_data = {
        "cid": data.get("cid"), # Frontend key name
        "name": data.get("name"), # Frontend key name
        "branch": data.get("branch"), # Frontend key name
        "type": data.get("type"), # Frontend key name
        "position": data.get("position"), # Frontend key name
        "related_to": data.get("related_to"), # Frontend key name
        "relationship": data.get("relationship") # Frontend key name
    }

    if not processed_data.get('name') or not processed_data.get('type') or not processed_data.get('branch'):
        return jsonify({"error": "Name, Type, and Branch are required fields."}), 400
    try:
        update_dosri_entry(dosri_id, processed_data)
        return jsonify({"message": f"DOSRI record {dosri_id} updated successfully."}), 200
    except Exception as e:
        print(f"Error updating DOSRI record {dosri_id} in CSV: {e}")
        return jsonify({"error": f"Failed to update DOSRI record: {str(e)}"}), 500

@operations_dosri_bp.route('/api/dosri/<int:dosri_id>', methods=['DELETE'])
def api_delete_dosri(dosri_id):
    """Deletes a DOSRI record from CSV."""
    try:
        delete_dosri_entry(dosri_id)
        return jsonify({"message": f"DOSRI record {dosri_id} deleted successfully."}), 200
    except Exception as e:
        print(f"Error deleting DOSRI record {dosri_id} from CSV: {e}")
        return jsonify({"error": f"Failed to delete DOSRI record: {str(e)}"}), 500

@operations_dosri_bp.route('/api/dosri/upload_csv', methods=['POST'])
def api_upload_dosri_csv():
    """Handles CSV file upload for DOSRI data, saving to CSV."""
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
            upload_dosri_csv_to_db(filepath, upload_option=upload_option)
            return jsonify({"message": f"DOSRI data uploaded successfully using '{upload_option}' option."}), 200
        except Exception as e:
            print(f"Error during DOSRI CSV upload: {e}")
            return jsonify({"error": f"Failed to upload CSV: {str(e)}"}), 500
        finally:
            shutil.rmtree(temp_dir)
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

@operations_dosri_bp.route('/api/dosri_list', methods=['GET'])
def api_get_dosri_list_summary():
    """
    API endpoint to retrieve the list of DOSRI members for summary reports.
    Fetches data from the CSV using get_dosri_data and returns it formatted for the frontend.
    """
    try:
        # Fetch all DOSRI data (now from CSV)
        dosri_list = get_dosri_data()

        # Format the data to match the expected structure for frontend summary requests
        # The frontend operations_dosri.js expects 'branch', 'cid' keys, and now 'type'
        formatted_dosri_members = []
        for member in dosri_list:
            formatted_type = member.get("type") # Get the type before potential modification
            if formatted_type == 'Related Interest':
                related_to = member.get("related_to", "")
                relationship = member.get("relationship", "")
                formatted_type = f"{formatted_type} ({related_to} - {relationship})"

            formatted_dosri_members.append({
                "branch": member.get("branch"),
                "cid": member.get("cid"),
                "name": member.get("name"),
                "type": formatted_type # Use the potentially modified type
            })

        return jsonify({"dosri_members": formatted_dosri_members}), 200
    except Exception as e:
        print(f"Error fetching DOSRI list for summary: {e}")
        return jsonify({"error": f"Failed to retrieve DOSRI list for summary: {str(e)}"}), 500


@operations_dosri_bp.route('/api/dosri/loan_balances', methods=['POST'])
def api_process_dosri_loan_balances():
    """
    API endpoint to process DOSRI loan balances.
    Calls the backend processing logic from operations_dosri.py.
    Now accepts 'report_date' from the request JSON.
    """
    data = request.get_json()
    dosri_members = data.get('dosri_members', [])
    report_date = data.get('report_date') # Get the report_date

    # Pass the report_date to the processing function
    return process_dosri_loan_balances(dosri_members=dosri_members, report_date=report_date)

@operations_dosri_bp.route('/api/dosri/deposit_liabilities', methods=['POST'])
def api_process_dosri_deposit_liabilities():
    """
    API endpoint to process DOSRI deposit liabilities.
    Calls the backend processing logic from operations_dosri.py.
    Now accepts 'report_date' from the request JSON.
    """
    data = request.get_json()
    dosri_members = data.get('dosri_members', [])
    report_date = data.get('report_date') # Get the report_date

    # Pass the report_date to the processing function
    return process_dosri_deposit_liabilities(dosri_members=dosri_members, report_date=report_date)

@operations_dosri_bp.route('/api/dosri/download_excel', methods=['POST'])
def api_download_dosri_excel_report():
    """
    Handles the POST request to download DOSRI data as an Excel file.
    Delegates the Excel generation to operations_dosri.download_dosri_excel_report.
    """
    try:
        # Call the actual Excel generation logic from operations_dosri.py
        # It expects request.json to be passed implicitly via Flask's request context
        return download_dosri_excel_report()
    except Exception as e:
        print(f"Error in api_download_dosri_excel_report route: {e}")
        return jsonify({"error": f"Failed to generate Excel report: {str(e)}"}), 500
