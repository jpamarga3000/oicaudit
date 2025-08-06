from flask import Blueprint, jsonify, session, request
from flask_cors import cross_origin
import traceback
import sys
import os

# The sys.path setup is now handled in app.py, so these lines are no longer needed here.
# # Get the directory of the current file (admin_database_routes.py)
# current_file_dir = os.path.dirname(os.path.abspath(__file__))
# # Construct the path to the 'backend' directory (parent of 'routes')
# backend_dir = os.path.dirname(current_file_dir)
# # Construct the path to the 'audit_tool' directory (parent of 'backend')
# project_root = os.path.dirname(backend_dir)
# # Add the project root to sys.path
# if project_root not in sys.path:
#     sys.path.append(project_root)
#     print(f"Added {project_root} to sys.path") # For debugging purposes

# Import the processing function
# This import should now work correctly because 'audit_tool' is in sys.path (due to app.py's setup)
from backend.admin_database_process import get_database_summary_data

admin_database_bp = Blueprint('admin_database_bp', __name__)

@admin_database_bp.route('/get_database_summary', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_database_summary_route():
    try:
        # Get force_refresh parameter from query string, default to False
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        # Authentication check (optional, but good practice for admin routes)
        # In a production environment, you would use @login_required or similar.
        # For now, we'll allow access for testing, but print a warning if not authenticated.
        # if 'username' not in session:
        #     print("WARNING: Access to /get_database_summary without authentication.")
        #     return jsonify({"success": False, "message": "Unauthorized access."}), 401

        summary_data = get_database_summary_data(force_refresh=force_refresh)
        
        if summary_data:
            return jsonify({"success": True, "data": summary_data}), 200
        else:
            return jsonify({"success": False, "message": "No database summary data found or an error occurred."}), 404

    except Exception as e:
        print(f"Error in /get_database_summary route: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": "An internal server error occurred while fetching database summary."}), 500
