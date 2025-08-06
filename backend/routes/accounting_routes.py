# audit_tool/backend/routes/accounting_routes.py
from flask import Blueprint, request, jsonify
import traceback

# Import processing functions
from backend.accounting_process import get_gl_names_and_codes_from_file, process_gl_report
from backend.trial_balance_process import get_tb_as_of_dates, process_trial_balance_data
from backend.reference_process import process_ref_report
from backend.description_process import process_desc_report
from backend.trend_process import process_trend_report # Keep this import if it's used elsewhere for other trend reports
from backend.financial_statement_process import process_financial_statement, get_financial_statement_trend_data # Import the new function
from backend.db_common import AREA_BRANCH_MAP # Import AREA_BRANCH_MAP from db_common

accounting_bp = Blueprint('accounting', __name__)

@accounting_bp.route('/get_gl_names_and_codes', methods=['GET'])
def get_gl_names_and_codes():
    branch = request.args.get('branch')
    if not branch:
        return jsonify({"message": "Branch parameter is required."}), 400

    try:
        gl_data = get_gl_names_and_codes_from_file(branch)
        return jsonify({"data": gl_data}), 200
    except Exception as e:
        print(f"Error fetching GL names and codes for branch {branch}: {e}")
        return jsonify({"message": f"Failed to fetch GL names and codes: {str(e)}"}), 500

@accounting_bp.route('/process_accounting_gl', methods=['POST'])
def process_accounting_gl():
    branch = request.form.get('branch')
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    gl_code = request.form.get('gl_code')

    if not all([branch, from_date, to_date, gl_code]):
        return jsonify({"message": "All parameters (branch, from_date, to_date, gl_code) are required."}), 400

    gl_code_raw = gl_code.replace('-', '')

    try:
        report_data = process_gl_report(branch, from_date, to_date, gl_code_raw)
        if report_data:
            return jsonify({"message": "GL Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing GL report: {e}")
        return jsonify({"message": f"An error occurred during GL report processing: {str(e)}"}), 500

@accounting_bp.route('/process_accounting_ref', methods=['POST'])
def process_accounting_ref():
    branch = request.form.get('branch')
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    reference_lookup = request.form.get('reference_lookup')
    match_type = request.form.get('match_type')

    if not all([branch, from_date, to_date, reference_lookup, match_type]):
        return jsonify({"message": "All parameters (branch, from_date, to_date, reference_lookup, match_type) are required."}), 400

    try:
        report_data = process_ref_report(branch, from_date, to_date, reference_lookup, match_type)
        if report_data:
            return jsonify({"message": "Reference Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing Reference report: {e}")
        return jsonify({"message": f"An error occurred during Reference report processing: {str(e)}"}), 500

@accounting_bp.route('/process_accounting_desc', methods=['POST'])
def process_accounting_desc():
    branch = request.form.get('branch')
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    description_lookup = request.form.get('description_lookup')
    match_type = request.form.get('match_type')

    if not all([branch, from_date, to_date, description_lookup, match_type]):
        return jsonify({"message": "All parameters (branch, from_date, to_date, description_lookup, match_type) are required."}), 400

    try:
        report_data = process_desc_report(branch, from_date, to_date, description_lookup, match_type)
        if report_data:
            return jsonify({"message": "Description Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing Description report: {e}")
        return jsonify({"message": f"An error occurred during Description report processing: {str(e)}"}), 500

@accounting_bp.route('/process_accounting_trend', methods=['POST'])
def process_accounting_trend():
    branch = request.form.get('branch')
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    gl_code = request.form.get('gl_code')
    frequency = request.form.get('frequency')

    if not all([branch, from_date, to_date, gl_code, frequency]):
        return jsonify({"message": "All parameters (branch, from_date, to_date, gl_code, frequency) are required."}), 400

    gl_code_raw = gl_code.replace('-', '')

    try:
        report_data = process_trend_report(branch, from_date, to_date, gl_code_raw, frequency)
        if report_data:
            return jsonify({"message": "Trend Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing Trend report: {e}")
        return jsonify({"message": f"An error occurred during Trend report processing: {str(e)}"}), 500

@accounting_bp.route('/get_tb_as_of_dates', methods=['GET'])
def get_tb_as_of_dates_endpoint():
    branch = request.args.get('branch')
    if not branch:
        return jsonify({"message": "Branch parameter is required."}), 400
    try:
        dates = get_tb_as_of_dates(branch)
        return jsonify({"data": dates}), 200
    except Exception as e:
        print(f"Error fetching TB As Of Dates for branch {branch}: {e}")
        return jsonify({"message": f"Failed to fetch TB As Of Dates: {str(e)}"}), 500

@accounting_bp.route('/process_trial_balance', methods=['POST'])
def process_trial_balance_endpoint():
    branch = request.form.get('branch')
    as_of_date_filename = request.form.get('as_of_date')

    if not all([branch, as_of_date_filename]):
        return jsonify({"message": "Branch and As Of Date are required."}), 400

    try:
        report_data = process_trial_balance_data(branch, as_of_date_filename)
        if report_data:
            return jsonify({"message": "Trial Balance Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing Trial Balance report: {e}")
        return jsonify({"message": f"An error occurred during Trial Balance report processing: {str(e)}"}), 500

@accounting_bp.route('/financial_statement', methods=['POST', 'OPTIONS'])
def financial_statement_endpoint():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    area = data.get('area') # NEW: Get area from the request
    branch = data.get('branch')
    date = data.get('date')

    if not all([area, branch, date]): # NEW: Validate area as well
        return jsonify({"status": "error", "message": "Area, Branch, and Date are required."}), 400

    try:
        # NEW: Pass area to the processing function
        fs_data = process_financial_statement(branch, date, area)
        if fs_data:
            return jsonify({"status": "success", "message": "Financial Statement generated successfully!", "data": fs_data}), 200
        else:
            return jsonify({"status": "error", "message": "No financial statement data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing financial statement: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"An error occurred during financial statement processing: {str(e)}"}), 500

@accounting_bp.route('/financial_statement/trend', methods=['GET'])
def financial_statement_trend_endpoint():
    """
    API endpoint to get detailed trend data for a specific account in the Financial Statement.
    """
    area = request.args.get('area')
    branch = request.args.get('branch')
    date = request.args.get('date')
    account_label = request.args.get('account_label')
    report_type = request.args.get('report_type') # 'financial_position' or 'financial_performance'

    if not all([area, branch, date, account_label, report_type]):
        return jsonify({"status": "error", "message": "Area, Branch, Date, Account Label, and Report Type are required."}), 400

    try:
        trend_data = get_financial_statement_trend_data(branch, date, area, account_label, report_type)
        if trend_data:
            return jsonify({"status": "success", "message": "Trend data fetched successfully!", "data": trend_data}), 200
        else:
            return jsonify({"status": "error", "message": "No trend data found for the specified account and criteria."}), 200
    except Exception as e:
        print(f"Error fetching financial statement trend data: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"An error occurred while fetching trend data: {str(e)}"}), 500
