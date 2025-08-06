from flask import Blueprint, request, jsonify
import traceback

# Import helper functions from the new utils module using absolute import
import backend.utils.helpers as helpers

# Import necessary functions/constants from db_common.py
from db_common import get_db_connection

# Import processing functions
from operations_dl import (
    generate_deposit_liabilities_report_logic, get_deposit_maturity_requirements_from_db,
    save_deposit_maturity_requirements_to_db, delete_deposit_maturity_requirement_from_db,
    get_deposit_interest_rates_from_db, save_deposit_interest_rates_to_db,
    delete_deposit_interest_rate_from_db,
    read_deposit_code_csv_products,
    generate_matured_deposits_report_logic, generate_wrong_application_interest_report_logic
)

operations_dl_bp = Blueprint('operations_dl', __name__)

@operations_dl_bp.route('/generate_deposit_liabilities_report', methods=['POST'])
def generate_deposit_liabilities_report_endpoint():
    data = request.get_json()
    area = data.get('area')
    branch = data.get('branch')

    branches_to_process = helpers.get_branches_for_request(area, branch)

    if not branches_to_process:
        return jsonify({"message": "No branches selected or invalid selection for Deposit Liabilities Report.", "data": []}), 400

    try:
        report_data = generate_deposit_liabilities_report_logic(branches_to_process)
        return jsonify(report_data), 200
    except Exception as e:
        print(f"Error processing Deposit Liabilities Report: {e}")
        return jsonify({"message": f"An error occurred during Deposit Liabilities Report processing: {str(e)}", "data": []}), 500

@operations_dl_bp.route('/get_deposit_maturity_requirements', methods=['GET'])
def get_deposit_maturity_requirements():
    conn = None # Initialize conn to None
    try:
        conn = get_db_connection()
        data = get_deposit_maturity_requirements_from_db()
        return jsonify({"data": data}), 200
    except Exception as e:
        print(f"Error in API /get_deposit_maturity_requirements: {e}")
        return jsonify({"message": f"Failed to get maturity requirements: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@operations_dl_bp.route('/save_deposit_maturity_requirements', methods=['POST'])
def save_deposit_maturity_requirements():
    conn = None # Initialize conn to None
    data = request.get_json()
    try:
        conn = get_db_connection()
        result = save_deposit_maturity_requirements_to_db(data)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in API /save_deposit_maturity_requirements: {e}")
        return jsonify({"message": f"Failed to save maturity requirements: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@operations_dl_bp.route('/delete_deposit_maturity_requirement', methods=['DELETE'])
def delete_deposit_maturity_requirement():
    conn = None # Initialize conn to None
    item_id = request.args.get('id')
    if not item_id:
        return jsonify({"message": "ID query parameter is required for deletion."}), 400

    try:
        conn = get_db_connection()
        result = delete_deposit_maturity_requirement_from_db(item_id)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error deleting deposit maturity requirement from DB: {e}")
        if conn:
            conn.rollback()
        return jsonify({"message": f"Failed to delete maturity requirement: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@operations_dl_bp.route('/get_deposit_interest_rates', methods=['GET'])
def get_deposit_interest_rates():
    conn = None # Initialize conn to None
    try:
        conn = get_db_connection()
        data = get_deposit_interest_rates_from_db()
        return jsonify({"data": data}), 200
    except Exception as e:
        print(f"Error in API /get_deposit_interest_rates: {e}")
        return jsonify({"message": f"Failed to get interest rates: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@operations_dl_bp.route('/save_deposit_interest_rates', methods=['POST'])
def save_deposit_interest_rates():
    conn = None # Initialize conn to None
    data = request.get_json()
    try:
        conn = get_db_connection()
        result = save_deposit_interest_rates_to_db(data)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in API /save_deposit_interest_rates: {e}")
        return jsonify({"message": f"Failed to save interest rates: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@operations_dl_bp.route('/delete_deposit_interest_rate', methods=['DELETE'])
def delete_deposit_interest_rate():
    conn = None # Initialize conn to None
    item_id = request.args.get('id')
    if not item_id:
        return jsonify({"message": "ID is required."}), 400
    try:
        conn = get_db_connection()
        result = delete_deposit_interest_rate_from_db(item_id)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error deleting deposit interest rate from DB: {e}")
        if conn:
            conn.rollback()
        return jsonify({"message": f"Failed to delete interest rate: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@operations_dl_bp.route('/get_deposit_products_from_csv', methods=['GET'])
def get_deposit_products_from_csv():
    try:
        products = read_deposit_code_csv_products()
        return jsonify({"data": products}), 200
    except Exception as e:
        print(f"Error in API /get_deposit_products_from_csv: {e}")
        return jsonify({"message": f"Failed to get products from CSV: {str(e)}"}), 500

@operations_dl_bp.route('/generate_matured_deposits_report', methods=['POST'])
def generate_matured_deposits_report():
    data = request.get_json()
    branch = data.get('branch')
    month = data.get('month')
    year = data.get('year')
    maturity_requirements_data = data.get('maturity_requirements_data', [])

    if not all([branch, month, year]):
        return jsonify({"message": "Branch, month, and year are required for Matured Deposits Report."}), 400

    try:
        report_data = generate_matured_deposits_report_logic(branch, month, year, maturity_requirements_data)
        return jsonify(report_data), 200
    except Exception as e:
        print(f"Error in API /generate_matured_deposits_report: {e}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@operations_dl_bp.route('/generate_wrong_application_interest_report', methods=['POST'])
def generate_wrong_application_interest_report():
    data = request.get_json()
    branch = data.get('branch')
    month = data.get('month')
    year = data.get('year')
    interest_rates_data = data.get('interest_rates_data', [])

    if not all([branch, month, year]):
        return jsonify({"message": "Branch, month, and year are required for Wrong Application of Interest Report."}), 400

    try:
        report_data = generate_wrong_application_interest_report_logic(branch, month, year, interest_rates_data)
        return jsonify(report_data), 200
    except Exception as e:
        print(f"Error in API /generate_wrong_application_interest_report: {e}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

