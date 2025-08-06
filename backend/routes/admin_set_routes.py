from flask import Blueprint, request, jsonify, session
import traceback
import pandas as pd # Import pandas for data handling
import os # Import os for path operations
from functools import wraps # NEW: Import wraps for decorators

# Import login settings functions from db_common.py
from backend.db_common import read_login_settings, write_login_settings, REGISTERED_USERS_PATH

admin_set_bp = Blueprint('admin_set', __name__, url_prefix='/admin')

# Helper function for authentication (can be replaced by a more robust decorator if available)
def admin_login_required(f):
    """
    Decorator to ensure the user is logged in and has admin access.
    For demonstration, we'll check if 'username' is in session.
    In a real application, you'd check a user's role/access code.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"success": False, "message": "Admin authentication required."}), 401
        
        # NEW: Check if the logged-in user has the 'AH' access code
        # This assumes 'access_code' is stored in the session upon successful login.
        if session.get('access_code') != 'AH':
            return jsonify({"success": False, "message": "Access denied. Only users with 'AH' access code can access settings."}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Route to get current login settings
@admin_set_bp.route('/login_settings', methods=['GET'])
# @admin_login_required # REMOVED: This GET route should not require authentication for the login page to fetch settings
def get_login_settings():
    """
    Retrieves the current biometric and OTP login settings.
    """
    try:
        settings = read_login_settings()
        # Explicitly convert boolean values to Python's native bool type
        # This helps in cases where pandas might return numpy.bool_ which isn't directly JSON serializable by Flask
        response_settings = {
            'biometric_login_enabled': bool(settings.get('biometric_login_enabled', True)),
            'otp_verification_enabled': bool(settings.get('otp_verification_enabled', True))
        }
        return jsonify({"success": True, **response_settings}), 200
    except Exception as e:
        print(f"Error getting login settings: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": "Failed to retrieve login settings."}), 500

# Route to update login settings
@admin_set_bp.route('/login_settings', methods=['POST'])
@admin_login_required # Kept: This POST route should still require admin authentication
def update_login_settings():
    """
    Updates the biometric and OTP login settings.
    Requires 'biometric_login_enabled' and 'otp_verification_enabled' boolean values in the request body.
    """
    data = request.get_json()
    biometric_enabled = data.get('biometric_login_enabled')
    otp_enabled = data.get('otp_verification_enabled')

    # Validate input types
    if not isinstance(biometric_enabled, bool) or not isinstance(otp_enabled, bool):
        return jsonify({"success": False, "message": "Invalid data types for settings. Must be boolean."}), 400

    try:
        settings_to_save = {
            'biometric_login_enabled': biometric_enabled,
            'otp_verification_enabled': otp_enabled
        }
        success = write_login_settings(settings_to_save)

        if success:
            return jsonify({"success": True, "message": "Login settings updated successfully."}), 200
        else:
            return jsonify({"success": False, "message": "Failed to save login settings."}), 500
    except Exception as e:
        print(f"Error updating login settings: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": "An error occurred while updating settings."}), 500
