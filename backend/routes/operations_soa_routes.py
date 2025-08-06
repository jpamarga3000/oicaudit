from flask import Blueprint, request, jsonify
import traceback

# Import processing functions
# FIX: Changed import to absolute path to match package structure
from backend.operations_soa import process_statement_of_account_report

operations_soa_bp = Blueprint('operations_soa', __name__)

@operations_soa_bp.route('/process_statement_of_account', methods=['POST'])
def process_statement_of_account_endpoint():
    branch = request.form.get('branch')
    # FIX: Removed type_input and category_input_code from request.form.get()
    # type_input = request.form.get('type_input')
    # category_input_code = request.form.get('category_input_code')
    from_date_str = request.form.get('from_date')
    to_date_str = request.form.get('to_date')
    account_lookup = request.form.get('account_lookup')
    code_lookup = request.form.get('code_lookup')
    description_lookup = request.form.get('description')
    trn_type_lookup = request.form.get('trn_type_lookup')
    match_type = request.form.get('match_type')

    # FIX: Updated validation condition to remove type_input and category_input_code
    if not all([branch, from_date_str, to_date_str]) or \
       not any([account_lookup, code_lookup, description_lookup, trn_type_lookup]):
        return jsonify({"message": "All parameters (Branch, From Date, To Date) are required, and at least one of Account Number, Code, Description, or TRN Type must be provided."}), 400

    try:
        # FIX: Updated the function call to match the new signature of process_statement_of_account_report
        report_data = process_statement_of_account_report(
            branch, from_date_str, to_date_str, account_lookup,
            code_lookup, description_lookup, trn_type_lookup, match_type
        )
        if report_data:
            return jsonify({"message": "Statement of Account generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing Statement of Account report: {e}")
        traceback.print_exc() # Print full traceback for debugging
        return jsonify({"message": f"An error occurred during Statement of Account report processing: {str(e)}"}), 500
