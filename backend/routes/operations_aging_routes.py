from flask import Blueprint, request, jsonify
import traceback

# Import helper functions from the new utils module using absolute import
import backend.utils.helpers as helpers

# Import processing functions
# FIX: Changed import to use absolute path 'backend.operations_process'
from backend.operations_process import get_aging_names_and_cids, get_aging_summary_data, get_aging_history_per_member_loan, \
    get_accounts_contribute_to_provisions_report, get_top_borrowers_report, \
    get_new_loans_with_past_due_history_report, get_new_loans_details
from backend.db_common import get_unique_aging_dates # NEW: Import function to get unique dates

operations_aging_bp = Blueprint('operations_aging', __name__)

@operations_aging_bp.route('/get_unique_aging_dates', methods=['GET'])
def get_unique_aging_dates_endpoint():
    area = request.args.get('area')
    branch = request.args.get('branch')

    branches_to_process = helpers.get_branches_for_request(area, branch)
    
    try:
        # Pass branches_to_process to filter unique dates by selected branch/area
        unique_dates = get_unique_aging_dates(branches_to_process)
        return jsonify({"data": unique_dates}), 200
    except Exception as e:
        print(f"Error fetching unique aging dates: {e}")
        return jsonify({"message": f"Failed to fetch unique dates: {str(e)}"}), 500


@operations_aging_bp.route('/get_aging_names_and_cids', methods=['GET'])
def get_aging_names_and_cids_endpoint():
    area = request.args.get('area')
    branch = request.args.get('branch')
    selected_date = request.args.get('selected_date') # NEW: Get selected_date from request

    # get_branches_for_request will return a list of specific branches,
    # or an empty list if 'ALL' or 'Consolidated' is selected (as Names/CIDs are per-branch specific)
    branches_to_process = helpers.get_branches_for_request(area, branch)

    if not branches_to_process:
        # If no specific branches are resolved (e.g., 'ALL' or 'Consolidated' is selected),
        # return empty data as Name/CID lookup is only for specific branches.
        return jsonify({"data": [], "message": "No specific branches resolved for Name/CID lookup (expected for ALL/Consolidated selections)."}), 200

    try:
        # Pass selected_date to the processing function
        data = get_aging_names_and_cids(branches_to_process, selected_date)
        return jsonify({"data": data}), 200
    except Exception as e:
        print(f"Error fetching Aging Names and CIDs for branches {branches_to_process}: {e}")
        return jsonify({"message": f"Failed to fetch Aging Names and CIDs: {str(e)}"}), 500

@operations_aging_bp.route('/get_aging_summary_data', methods=['GET'])
def get_aging_summary_data_endpoint():
    area = request.args.get('area')
    branch = request.args.get('branch')
    selected_date = request.args.get('selected_date') # NEW: Get selected_date from request

    # get_branches_for_request will return a list of specific branches,
    # or the special 'CONSOLIDATED' or 'ALL_BRANCHES_LIST' based on input.
    branches_to_process = helpers.get_branches_for_request(area, branch)

    if not branches_to_process:
        # If no valid branch/area combination, return default empty summary.
        return jsonify({"data": {
            "TOTAL CURRENT BALANCE": 0.0, "TOTAL PAST DUE": 0.0, "TOTAL Both Current and Past Due": 0.0, "AS OF DATE": "",
            "CURRENT_ACCOUNTS_COUNT": 0, "PAST_DUE_ACCOUNTS_COUNT": 0, "TOTAL_ACCOUNTS_COUNT": 0,
            "DELINQUENCY_RATE": 0.0, "PROVISION_1_365_DAYS_BALANCE": 0.0, "PROVISION_1_365_DAYS_ACCOUNTS_COUNT": 0,
            "PROVISION_OVER_365_DAYS_BALANCE": 0.0, "PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT": 0,
            "TOTAL_PROVISIONS": 0.0
        }, "message": "No branches selected or invalid selection for Summary Data."}), 200

    try:
        # Pass selected_date to the processing function
        summary_data = get_aging_summary_data(branches_to_process, selected_date)
        return jsonify({"data": summary_data}), 200
    except Exception as e:
        print(f"Error fetching Aging Summary Data for branches {branches_to_process}: {e}")
        return jsonify({"message": f"Failed to fetch Aging Summary Data: {str(e)}"}), 500

@operations_aging_bp.route('/get_aging_history_per_member_loan', methods=['POST'])
def get_aging_history_per_member_loan_endpoint():
    # For this report, 'area' is not directly used in the backend processing,
    # as it's always per-branch and per-CID. 'branch' should be a specific branch.
    branch = request.form.get('branch')
    cid = request.form.get('cid')
    selected_date = request.form.get('selected_date') # NEW: Get selected_date from request

    if not all([branch, cid]):
        return jsonify({"message": "Branch and CID are required for Aging History per Member's Loan."}), 400
    
    # Ensure branch is not 'ALL' or 'Consolidated' for this specific report
    if branch == 'ALL' or branch == 'Consolidated':
        return jsonify({"message": "Please select a specific Branch for Aging History per Member's Loan. 'Consolidated' or 'ALL' is not applicable here."}), 400


    try:
        # Pass selected_date to the processing function
        history_data = get_aging_history_per_member_loan(branch, cid, selected_date)
        if history_data:
            return jsonify({"message": "Aging History generated successfully!", "data": history_data}), 200
        else:
            return jsonify({"message": "No aging history data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing Aging History: {e}")
        return jsonify({"message": f"An error occurred during Aging History processing: {str(e)}"}), 500

@operations_aging_bp.route('/get_accounts_contribute_to_provisions_report', methods=['POST'])
def get_accounts_contribute_to_provisions_report_endpoint():
    area = request.form.get('area')
    branch = request.form.get('branch')
    selected_month = request.form.get('selected_month', type=int)
    selected_year = request.form.get('selected_year', type=int)
    selected_aging_category = request.form.get('selected_aging_category')
    selected_date = request.form.get('selected_date') # NEW: Get selected_date from request

    branches_to_process = helpers.get_branches_for_request(area, branch)

    # If not consolidated/all, month, year, and aging category are required
    is_consolidated_or_all = 'Consolidated' in branches_to_process or 'ALL_BRANCHES_LIST' in branches_to_process
    
    if not branches_to_process:
        return jsonify({"message": "Area/Branch selection is required for Provisions Report."}), 400

    if not is_consolidated_or_all and not all([selected_month, selected_year, selected_aging_category]):
        return jsonify({"message": "Month, Year, and Aging category are required for specific branch Provisions Report."}), 400

    try:
        # Pass selected_date to the processing function
        report_data = get_accounts_contribute_to_provisions_report(branches_to_process, selected_month, selected_year, selected_aging_category, selected_date)
        if report_data:
            return jsonify({"message": "Provisions Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing Provisions Report: {e}")
        return jsonify({"message": f"An error occurred during Provisions Report processing: {str(e)}"}), 500

@operations_aging_bp.route('/get_top_borrowers_report', methods=['POST'])
def get_top_borrowers_report_endpoint():
    area = request.form.get('area')
    branch = request.form.get('branch')
    status_filter = request.form.get('status_filter')
    selected_date = request.form.get('selected_date') # NEW: Get selected_date from request

    branches_to_process = helpers.get_branches_for_request(area, branch)

    # If not consolidated/all, status_filter is required
    is_consolidated_or_all = 'Consolidated' in branches_to_process or 'ALL_BRANCHES_LIST' in branches_to_process

    if not branches_to_process:
        return jsonify({"message": "Area/Branch selection is required for Top Borrowers Report."}), 400

    if not is_consolidated_or_all and not status_filter:
        return jsonify({"message": "Status is required for specific branch Top Borrowers Report."}), 400

    try:
        # Pass selected_date to the processing function
        report_data = get_top_borrowers_report(branches_to_process, status_filter, selected_date)
        if report_data:
            return jsonify({"message": "Top Borrowers Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified top borrowers criteria."}), 200
    except Exception as e:
        print(f"Error processing Top Borrowers Report: {e}")
        return jsonify({"message": f"An error occurred during Top Borrowers Report processing: {str(e)}"}), 500

@operations_aging_bp.route('/get_new_loans_with_past_due_history_report', methods=['POST'])
def get_new_loans_with_past_due_history_report_endpoint():
    area = request.form.get('area')
    branch = request.form.get('branch')
    selected_year = request.form.get('selected_year', type=int)
    selected_date = request.form.get('selected_date') # NEW: Get selected_date from request

    branches_to_process = helpers.get_branches_for_request(area, branch)

    # If not consolidated/all, year is required
    is_consolidated_or_all = 'Consolidated' in branches_to_process or 'ALL_BRANCHES_LIST' in branches_to_process

    if not branches_to_process:
        return jsonify({"message": "Area/Branch selection is required for New Loans with Past Due Credit History Report."}), 400

    if not is_consolidated_or_all and not selected_year:
        return jsonify({"message": "Year is required for specific branch New Loans with Past Due Credit History Report."}), 400

    try:
        # Pass selected_date to the processing function
        report_data = get_new_loans_with_past_due_history_report(branches_to_process, selected_year, selected_date)
        if report_data:
            return jsonify({"message": "New Loans with Past Due Credit History Report generated successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error processing New Loans with Past Due Credit History Report: {e}")
        return jsonify({"message": f"An error occurred during New Loans with Past Due Credit History Report processing: {str(e)}"}), 500

@operations_aging_bp.route('/get_new_loans_details', methods=['POST'])
def get_new_loans_details_endpoint():
    area = request.form.get('area')
    branch = request.form.get('branch')
    name = request.form.get('name')
    selected_year = request.form.get('selected_year', type=int)
    category_type = request.form.get('category_type')
    selected_date = request.form.get('selected_date') # NEW: Get selected_date from request

    # For new loans details, 'area' and 'branch' should resolve to a specific branch
    # as details are always per-member, per-branch.
    branches_to_process = helpers.get_branches_for_request(area, branch)

    if not branches_to_process or not name or not selected_year or not category_type:
        return jsonify({"message": "All parameters (Area/Branch, Name, Year, Category Type) are required for loan details."}), 400
    
    # Ensure branch is not 'ALL' or 'Consolidated' for this specific report
    if branch == 'ALL' or branch == 'Consolidated':
        return jsonify({"message": "Please select a specific Branch for Loan Details. 'Consolidated' or 'ALL' is not applicable here."}), 400

    try:
        # Pass selected_date to the processing function
        details_data = get_new_loans_details(branches_to_process, name, selected_year, category_type, selected_date)
        if details_data:
            return jsonify({"message": "Loan details fetched successfully!", "data": details_data}), 200
        else:
            return jsonify({"message": "No loan details found for the specified criteria."}), 200
    except Exception as e:
        print(f"Error fetching loan details: {e}")
        return jsonify({"message": f"An error occurred during loan details fetching: {str(e)}"}), 500
