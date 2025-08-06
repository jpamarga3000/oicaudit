# backend/routes/get_branches_routes.py
from flask import Blueprint, request, jsonify
from backend.db_common import AREA_BRANCH_MAP

get_branches_bp = Blueprint('get_branches', __name__)

@get_branches_bp.route('/get_branches', methods=['GET'])
def get_branches():
    """
    Returns a list of branches for a given area, based on the AREA_BRANCH_MAP.
    """
    area = request.args.get('area')
    
    # DEBUG: Log the received area parameter
    print(f"DEBUG: Received request for branches in area: '{area}'")
    
    if area and area in AREA_BRANCH_MAP:
        # Filter out 'CONSOLIDATED' if it's a special value in the map
        branches = [b for b in AREA_BRANCH_MAP[area] if b != 'CONSOLIDATED']
        
        # DEBUG: Log the branches found for the area
        print(f"DEBUG: Found {len(branches)} branches for area '{area}': {branches}")
        
        return jsonify({"branches": branches}), 200
    
    # DEBUG: Log if no area was found or if the area is not in the map
    print(f"DEBUG: No branches found for area '{area}'.")
    return jsonify({"branches": []}), 404
