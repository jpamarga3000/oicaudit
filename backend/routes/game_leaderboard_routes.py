# audit_tool/backend/routes/game_leaderboard_routes.py
from flask import Blueprint, request, jsonify, session
from flask_cors import cross_origin
import traceback
from backend.game_leaderboard_process import get_leaderboard_data, submit_game_score
from backend.db_common import get_user_first_name # To get user's first name

game_leaderboard_bp = Blueprint('game_leaderboard_bp', __name__)

@game_leaderboard_bp.route('/submit_game_score', methods=['POST'])
@cross_origin(supports_credentials=True)
def submit_game_score_route():
    try:
        data = request.get_json()
        score = data.get('score')
        
        # Get username from session (assuming user is logged in)
        username = session.get('username')
        if not username:
            # Fallback for testing or if session not fully integrated, but ideally login_required
            username = data.get('username', 'Guest') # Get username from payload if not in session
            print(f"Server Log (Leaderboard Route): No username in session, using provided: {username}")

        # Get the first name of the user from registered.csv
        player_name = get_user_first_name(username)
        if not player_name:
            player_name = username # Fallback to username if first name not found
            print(f"Server Log (Leaderboard Route): Could not get first name for {username}, using username as player name.")

        if score is None:
            return jsonify({"success": False, "message": "Score is required."}), 400

        success, message = submit_game_score(player_name, score)

        if success:
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"success": False, "message": message}), 500

    except Exception as e:
        print(f"Error in /submit_game_score route: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": "An internal server error occurred while submitting score."}), 500

@game_leaderboard_bp.route('/get_leaderboard', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_leaderboard_route():
    try:
        leaderboard = get_leaderboard_data()
        if leaderboard is not None:
            return jsonify({"success": True, "leaderboard": leaderboard}), 200
        else:
            return jsonify({"success": False, "message": "Could not retrieve leaderboard data."}), 500
    except Exception as e:
        print(f"Error in /get_leaderboard route: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": "An internal server error occurred while fetching leaderboard."}), 500

