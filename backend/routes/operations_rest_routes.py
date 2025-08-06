# audit_tool/backend/routes/operations_rest_routes.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin # Import cross_origin
import traceback

# Import the processing logic
from backend.operations_rest_process import get_restructured_loan_data_logic

operations_rest_bp = Blueprint('operations_rest', __name__)

@operations_rest_bp.route('/get_restructured_loan_data', methods=['POST'])
@cross_origin(supports_credentials=True) # Add this decorator for explicit CORS handling
def get_restructured_loan_data():
    """
    API endpoint to get restructured loan summary and details based on a report date.
    """
    data = request.get_json()
    report_date_str = data.get('report_date')

    if not report_date_str:
        return jsonify({"message": "Report date is required."}), 400

    try:
        result = get_restructured_loan_data_logic(report_date_str)
        # Check for error message from logic function (assuming logic function returns a dict with 'message' key)
        if "error" in result.get("message", "").lower(): 
            return jsonify(result), 500
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in /get_restructured_loan_data route: {e}")
        traceback.print_exc()
        return jsonify({"message": f"An unexpected server error occurred: {str(e)}"}, 500)

