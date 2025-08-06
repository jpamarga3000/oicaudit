# backend/routes/monitoring_routes.py
from flask import Blueprint, request, jsonify
import traceback

# Import helper functions from the new utils module
import backend.utils.helpers as helpers

# Import processing functions for this module
from backend.mon_reg_aud_process import get_regular_audit_report_data
# from backend.mon_spe_aud_process import get_special_audit_report_data

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/monitoring/regular_audit', methods=['POST'])
def get_regular_audit_report():
    try:
        data = request.json
        area = data.get('area')
        branch = data.get('branch')

        if not area and not branch:
            return jsonify({"message": "Area or Branch is required."}), 400

        # Replace the placeholder logic with a call to the actual processing function
        report_data = get_regular_audit_report_data(area, branch)

        if report_data:
            return jsonify({"message": "Regular Audit report processed successfully!", "data": report_data}), 200
        else:
            return jsonify({"message": "No data found for the selected criteria.", "data": []}), 200

    except Exception as e:
        print(f"Error processing regular audit report: {e}")
        traceback.print_exc()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@monitoring_bp.route('/monitoring/special_audit', methods=['POST'])
def get_special_audit_report():
    try:
        data = request.json
        area = data.get('area')
        branch = data.get('branch')

        if not area and not branch:
            return jsonify({"message": "Area or Branch is required."}), 400

        branches_to_process = helpers.get_branches_for_request(area, branch)

        # Placeholder logic: In a real implementation, you would call a processing function
        # from backend.mon_spe_aud_process.py here to get the data.
        print(f"Server Log: Processing Special Audit report for branches: {branches_to_process}")

        # Replace this with a call to your actual processing function
        # report_data = get_special_audit_report_data(branches_to_process)
        report_data = [
            {"column1": "Special Audit Data 1", "column2": "Value A", "column3": "Extra Info A"},
            {"column1": "Special Audit Data 2", "column2": "Value B", "column3": "Extra Info B"}
        ]

        return jsonify({"message": "Special Audit report processed successfully!", "data": report_data}), 200

    except Exception as e:
        print(f"Error processing special audit report: {e}")
        traceback.print_exc()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
