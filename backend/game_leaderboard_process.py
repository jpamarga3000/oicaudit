# audit_tool/backend/game_leaderboard_process.py
import pandas as pd
import os
from backend.db_common import GAME_SCORE_CSV_PATH, read_csv_to_dataframe, write_dataframe_to_csv

def get_leaderboard_data():
    """
    Reads the game_score.csv, sorts it by SCORE (highest to lowest),
    and returns the leaderboard data.
    """
    try:
        df = read_csv_to_dataframe(GAME_SCORE_CSV_PATH)
        if df.empty:
            print("Server Log (Leaderboard): game_score.csv is empty or not found.")
            return []

        # Ensure SCORE column is numeric for sorting
        df['SCORE'] = pd.to_numeric(df['SCORE'], errors='coerce').fillna(0)
        
        # Sort by SCORE in descending order
        df_sorted = df.sort_values(by='SCORE', ascending=False).reset_index(drop=True)
        
        # Convert to list of dictionaries for JSON serialization
        leaderboard_data = df_sorted.to_dict(orient='records')
        print(f"Server Log (Leaderboard): Retrieved {len(leaderboard_data)} leaderboard entries.")
        return leaderboard_data
    except Exception as e:
        print(f"Server Log (Leaderboard): Error getting leaderboard data: {e}")
        return []

def submit_game_score(player_name, score):
    """
    Submits a new game score to game_score.csv.
    If the player already exists and the new score is higher, it updates the score.
    Otherwise, it adds a new entry.
    """
    try:
        df = read_csv_to_dataframe(GAME_SCORE_CSV_PATH)
        
        # Ensure SCORE column is numeric for comparison
        df['SCORE'] = pd.to_numeric(df['SCORE'], errors='coerce').fillna(0)

        # Check if player already exists
        player_exists = False
        if not df.empty and 'NAME' in df.columns:
            # Find the row(s) for the current player
            player_rows = df[df['NAME'] == player_name]
            if not player_rows.empty:
                # Get the highest score for the existing player
                existing_highest_score = player_rows['SCORE'].max()

                if score > existing_highest_score:
                    # Update the existing player's score to the new, higher score
                    # This will set the score for ALL entries of that player to the new highest.
                    # To keep only one entry per player with the highest score,
                    # we'll first remove all existing entries for the player, then add the new one.
                    df = df[df['NAME'] != player_name] # Remove old entries for this player
                    print(f"Server Log (Leaderboard): Updating score for {player_name} from {existing_highest_score} to {score}.")
                else:
                    player_exists = True # Keep existing entry if new score is not higher
                    print(f"Server Log (Leaderboard): New score {score} for {player_name} is not higher than existing highest score {existing_highest_score}. Not updating.")
        
        if not player_exists or (player_exists and score > existing_highest_score):
            # Create a new DataFrame for the new score (or updated score)
            new_score_df = pd.DataFrame([{'NAME': player_name, 'SCORE': score}])
            
            # Concatenate the existing (potentially filtered) DataFrame with the new score
            df_updated = pd.concat([df, new_score_df], ignore_index=True)
        else:
            df_updated = df # No update needed, keep the original DataFrame

        # Ensure SCORE column is numeric before saving
        df_updated['SCORE'] = pd.to_numeric(df_updated['SCORE'], errors='coerce').fillna(0)

        if write_dataframe_to_csv(df_updated, GAME_SCORE_CSV_PATH):
            print(f"Server Log (Leaderboard): Successfully submitted/updated score for {player_name}: {score}")
            return True, "Score submitted successfully."
        else:
            print(f"Server Log (Leaderboard): Failed to submit/update score for {player_name}: {score}")
            return False, "Failed to submit score."
    except Exception as e:
        print(f"Server Log (Leaderboard): Error submitting game score: {e}")
        import traceback
        traceback.print_exc()
        return False, f"An error occurred while submitting score: {e}"

