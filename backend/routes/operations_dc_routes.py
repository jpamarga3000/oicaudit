from flask import Blueprint, request, jsonify, send_file
import json
import pandas as pd
from datetime import datetime
import io
import traceback
import uuid # Import the uuid module

# Import necessary functions/constants from db_common.py
from db_common import get_db_connection, format_currency_py, AREA_BRANCH_MAP
# Import helper functions from the new utils module using absolute import
import backend.utils.helpers as helpers

# Import processing functions
# MODIFIED: Changed to absolute import for clarity and to prevent potential import issues
from backend.operations_dc import generate_deposit_counterpart_report_logic

operations_dc_bp = Blueprint('operations_dc', __name__)

@operations_dc_bp.route('/get_default_deposit_requirements', methods=['GET'])
def get_default_deposit_requirements():
    """
    Fetches default deposit counterpart requirements from the SQL database.
    """
    conn = None # Initialize conn to None
    requirements = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, product, `condition`, deposit_counterpart_json FROM dc_req")
            result = cursor.fetchall()
            for row in result:
                row_dict = dict(row)
                if row_dict['deposit_counterpart_json']:
                    row_dict['depositCounterpart'] = json.loads(row_dict['deposit_counterpart_json'])
                else:
                    row_dict['depositCounterpart'] = {}
                del row_dict['deposit_counterpart_json']
                requirements.append(row_dict)
        return jsonify({"data": requirements}), 200
    except Exception as e:
        print(f"Error fetching default deposit requirements from DB: {e}")
        return jsonify({"message": f"Failed to fetch default requirements: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@operations_dc_bp.route('/save_deposit_requirements', methods=['POST'])
def save_deposit_requirements():
    """
    Saves the provided deposit counterpart requirements to the SQL database.
    This replaces all existing entries in the dc_req table.
    """
    conn = None # Initialize conn to None
    requirements_data = request.get_json()
    
    # --- DEBUGGING: Print incoming data ---
    print(f"Server Log: Received requirements data for saving: {json.dumps(requirements_data, indent=2)}")
    # --- END DEBUGGING ---

    if not isinstance(requirements_data, list):
        return jsonify({"message": "Invalid data format. Expected a list of requirements."}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # It's generally better to update/insert individually or use ON DUPLICATE KEY UPDATE
            # if you want to preserve existing data and only update/add.
            # If the intention is truly to replace all, then DELETE FROM is correct.
            # For now, keeping DELETE FROM as per original logic.
            cursor.execute("DELETE FROM dc_req")

            for req in requirements_data:
                # Validate product and condition before processing
                product = req.get('product')
                condition = req.get('condition')

                if not product or not condition:
                    print(f"Server Log: Skipping invalid requirement due to missing product or condition: {req}")
                    continue # Skip this requirement if product or condition is empty

                # Generate a new UUID if 'id' is not present or is empty
                req_id = req.get('id')
                if not req_id:
                    req_id = str(uuid.uuid4()) # Generate a unique ID
                    print(f"Server Log: Generated new ID for requirement: {req_id}")

                deposit_counterpart_json = json.dumps(req.get('depositCounterpart', {}))

                cursor.execute(
                    "INSERT INTO dc_req (id, product, `condition`, deposit_counterpart_json) VALUES (%s, %s, %s, %s)",
                    (req_id, product, condition, deposit_counterpart_json)
                )
            conn.commit()
        return jsonify({"message": "Deposit requirements saved successfully to SQL."}), 200
    except ValueError as ve:
        print(f"Server Log: Data validation error during save: {str(ve)}")
        return jsonify({"message": f"Data validation error: {str(ve)}"}), 400
    except Exception as e:
        print(f"Error saving deposit requirements to DB: {e}")
        traceback.print_exc() # Print full traceback for detailed debugging
        if conn:
            conn.rollback()
        return jsonify({"message": f"Failed to save requirements to SQL: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


@operations_dc_bp.route('/generate_deposit_counterpart_report', methods=['POST'])
def generate_deposit_counterpart_report():
    data = request.get_json()
    selected_branch_or_area = data.get('branch') # This can be a single branch or an area name
    report_date = data.get('report_date')
    deposit_requirements_data = data.get('deposit_requirements_data', [])
    area = data.get('area') # NEW: Get area from payload

    if not report_date:
        return jsonify({"message": "Report date is required."}), 400

    # Parse the report_date string into datetime object
    try:
        report_datetime = datetime.strptime(report_date, '%m/%d/%Y')
    except ValueError:
        return jsonify({"message": "Invalid date format. Expected MM/DD/YYYY."}), 400

    # Determine the actual list of branches to pass to the logic function
    branches_for_logic = helpers.get_branches_for_request(area, selected_branch_or_area)

    if not branches_for_logic:
        return jsonify({"message": "Branch or Area is required."}), 400

    # Pass the original selected entity (branch or area) to the logic function
    report_data = generate_deposit_counterpart_report_logic(branches_for_logic, report_date, deposit_requirements_data, selected_branch_or_area)

    return jsonify(report_data)

@operations_dc_bp.route('/download_deposit_counterpart_excel', methods=['POST'])
def download_deposit_counterpart_excel():
    data = request.get_json()
    selected_branch_or_area = data.get('branch') # This can be a single branch or an area name
    report_date = data.get('report_date')
    deposit_requirements_data = data.get('deposit_requirements_data', [])
    area = data.get('area') # NEW: Get area from payload

    if not all([selected_branch_or_area, report_date]):
        return jsonify({"message": "Branch/Area and report date are required for Excel download."}), 400

    # Parse the report_date string into datetime object
    try:
        report_datetime = datetime.strptime(report_date, '%m/%d/%Y')
    except ValueError:
        return jsonify({"message": "Invalid date format. Expected MM/DD/YYYY."}), 400

    # Determine the actual list of branches to pass to the logic function
    branches_for_logic = helpers.get_branches_for_request(area, selected_branch_or_area)

    if not branches_for_logic:
        return jsonify({"message": "Branch or Area is required."}), 400

    try:
        # Pass the original selected entity (branch or area) to the logic function
        report_results = generate_deposit_counterpart_report_logic(branches_for_logic, report_date, deposit_requirements_data, selected_branch_or_area)

        df_mb = pd.DataFrame(report_results.get('member_borrowers_data', []))
        df_details = pd.DataFrame(report_results.get('details_data', []))

        df_def_dc = pd.DataFrame()
        if not df_mb.empty:
            df_mb['DC_COMPLIANCE_NUM'] = pd.to_numeric(df_mb['DC_COMPLIANCE'], errors='coerce').fillna(0)
            df_mb['TOTAL_DC_NUM'] = pd.to_numeric(df_mb['TOTAL_DC'], errors='coerce').fillna(0)

            df_def_dc = df_mb[
                (df_mb['DC_COMPLIANCE_NUM'] < 100) &
                (df_mb['TOTAL_DC_NUM'] > 0)
            ].copy()
            df_def_dc.drop(columns=['DC_COMPLIANCE_NUM', 'TOTAL_DC_NUM'], errors='ignore', inplace=True)

        df_def_tdc = pd.DataFrame()
        if not df_mb.empty:
            df_mb['TDC_COMPLIANCE_NUM'] = pd.to_numeric(df_mb['TDC_COMPLIANCE'], errors='coerce').fillna(0)
            df_mb['TOTAL_TDC_NUM'] = pd.to_numeric(df_mb['TOTAL_TDC'], errors='coerce').fillna(0)

            df_def_tdc = df_mb[
                (df_mb['TDC_COMPLIANCE_NUM'] < 100) &
                (df_mb['TOTAL_TDC_NUM'] > 0)
            ].copy()
            df_def_tdc.drop(columns=['DC_COMPLIANCE_NUM', 'TOTAL_TDC_NUM'], errors='ignore', inplace=True)


        columns_to_format_mb = [
            'LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE',
            'DEPOSITS_REGULAR_SAVINGS', 'DEPOSITS_SHARE_CAPITAL', 'DEPOSITS_ATM', 'DEPOSITS_CSD', 'DEPOSITS_TOTAL',
            'TOTAL_DC', 'TIME_DEPOSITS_BALANCE', 'TOTAL_TDC'
        ]

        for col in columns_to_format_mb:
            if col in df_mb.columns:
                # Ensure the column is numeric before applying format_currency_py
                df_mb[col] = pd.to_numeric(df_mb[col], errors='coerce').apply(lambda x: format_currency_py(x) if pd.notna(x) else '')
        if 'DC_COMPLIANCE' in df_mb.columns:
            df_mb['DC_COMPLIANCE'] = df_mb['DC_COMPLIANCE'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '')
        if 'TDC_COMPLIANCE' in df_mb.columns:
            df_mb['TDC_COMPLIANCE'] = df_mb['TDC_COMPLIANCE'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '')

        columns_to_format_details = ['PRINCIPAL', 'BALANCE', 'DC_REQ']
        for col in columns_to_format_details:
            if col in df_details.columns:
                # Ensure the column is numeric before applying format_currency_py
                df_details[col] = pd.to_numeric(df_details[col], errors='coerce').apply(lambda x: format_currency_py(x) if pd.notna(x) else '')

        for col in ['DISBURSED', 'MATURITY']:
            if col in df_details.columns:
                # Ensure the column is datetime before formatting
                df_details[col] = pd.to_datetime(df_details[col], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')

        mb_excel_headers = [
            'CID', 'NAME', 'BRANCH',
            'LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE',
            'DEPOSITS_REGULAR_SAVINGS', 'DEPOSITS_SHARE_CAPITAL', 'DEPOSITS_ATM', 'DEPOSITS_CSD', 'DEPOSITS_TOTAL',
            'TOTAL_DC', 'TIME_DEPOSITS_BALANCE', 'TOTAL_TDC', 'DC_COMPLIANCE', 'TDC_COMPLIANCE', 'ACCOUNTS_COUNT'
        ]

        details_excel_headers = [
            'NAME', 'CID', 'ACCOUNT', 'PRINCIPAL', 'BALANCE', 'DISBURSED', 'MATURITY', 'PRODUCT', 'AGING', 'DC_CONDITIONS', 'DC_REQ'
        ]

        df_mb = df_mb.reindex(columns=mb_excel_headers, fill_value='')
        df_details = df_details.reindex(columns=details_excel_headers, fill_value='')
        df_def_dc = df_def_dc.reindex(columns=mb_excel_headers, fill_value='')
        df_def_tdc = df_def_tdc.reindex(columns=mb_excel_headers, fill_value='')

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_mb.to_excel(writer, sheet_name='MB', index=False)
            df_details.to_excel(writer, sheet_name='DETAILS', index=False)
            df_def_dc.to_excel(writer, sheet_name='DEF_DC', index=False)
            df_def_tdc.to_excel(writer, sheet_name='DEF_TDC', index=False)

        output.seek(0)

        # Format filename using the full date
        filename_date = datetime.strptime(report_date, '%m/%d/%Y').strftime('%m-%d-%Y')
        
        filename_prefix = ''
        if selected_branch_or_area == 'CONSOLIDATED':
            filename_prefix = 'CONSOLIDATED'
        elif selected_branch_or_area.startswith('Area'):
            filename_prefix = selected_branch_or_area.upper().replace(' ', '_')
        else:
            filename_prefix = selected_branch_or_area.upper()

        filename = f"{filename_prefix} DEPOSIT COUNTERPART - {filename_date}.xlsx"

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)

    except Exception as e:
        print(f"Error generating Excel for Deposit Counterpart Report: {e}")
        return jsonify({"message": f"An error occurred during Excel generation: {str(e)}"}), 500

