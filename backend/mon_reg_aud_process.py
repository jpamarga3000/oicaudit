# backend/mon_reg_aud_process.py
import pandas as pd
import pymysql.cursors
import os
import traceback
from datetime import datetime
from backend.db_common import get_db_connection_sqlalchemy
from sqlalchemy import text # NEW: Import text from sqlalchemy

def get_regular_audit_report_data(area, branch):
    """
    Fetches the Regular Audit report data from the `finding_report` table,
    then calculates the status based on a lookup in the `finding_audit` table.
    
    Args:
        area (str): The selected area.
        branch (str): The selected branch.
        
    Returns:
        list: A list of dictionaries representing the report data with calculated status.
    """
    print(f"Server Log: Fetching regular audit data for Area: {area}, Branch: {branch}")
    
    engine = get_db_connection_sqlalchemy()
    if engine is None:
        return []

    try:
        # Determine the area value to use in the query.
        query_area = area
        if area != 'Consolidated':
            try:
                # Extract the number from the string 'Area 1'
                query_area = int(area.split(' ')[1])
            except (IndexError, ValueError):
                # Fallback in case the area is already a numerical string, e.g., '1'
                query_area = int(area)

        # Columns to select from finding_report. Note: Status is not selected here as it's calculated.
        # We assume the column names in the DB are `Year_Audited` and `Finding_ID` and `Risk_No` based on previous errors.
        columns_to_select = ["`Area`", "`Branch`", "`Year_Audited`", "`Area_Audited`", "`Finding_ID`", "`Risk_No`", "`Risk_Event`", "`Risk_Level`"]

        if area == 'Consolidated':
            query = f"SELECT {', '.join(columns_to_select)} FROM finding_report"
            df = pd.read_sql(query, engine)
        else:
            query = f"SELECT {', '.join(columns_to_select)} FROM finding_report WHERE `Area` = :area AND `Branch` = :branch"
            params = {'area': query_area, 'branch': branch}
            
            print(f"DEBUG SQL: Executing query: {query}")
            print(f"DEBUG SQL: With parameters: {params}")
            
            df = pd.read_sql(text(query), engine, params=params)

        if df.empty:
            print("DEBUG: DataFrame is empty, returning empty list.")
            return []

        # List to hold the final results with the calculated status
        final_report_data = []

        # Iterate through each row of the finding_report data to calculate the status
        for _, row in df.iterrows():
            # Get the lookup values from the current row
            lookup_branch = row['Branch']
            lookup_year = row['Year_Audited']
            lookup_finding_id = row['Finding_ID']
            lookup_risk_id = row['Risk_No'] # Assuming Risk_No is the Risk ID

            # Query the finding_audit table to get status data
            status_query = text("""
                SELECT `Status`
                FROM `finding_audit`
                WHERE `Branch` = :branch
                AND `Year_Audited` = :year_audited
                AND `Finding_ID` = :finding_id
                AND `Risk_ID` = :risk_id
            """)
            status_params = {
                'branch': lookup_branch,
                'year_audited': lookup_year,
                'finding_id': lookup_finding_id,
                'risk_id': lookup_risk_id
            }

            status_df = pd.read_sql(status_query, engine, params=status_params)
            
            total_audits = len(status_df)
            if total_audits > 0:
                closed_audits = len(status_df[status_df['Status'] == 'Closed'])
                closed_percentage = (closed_audits / total_audits) * 100
                
                if closed_percentage == 0:
                    status = 'Open'
                elif closed_percentage == 100:
                    status = 'Closed'
                else:
                    status = 'In Progress'
            else:
                status = 'Open' # Default to 'Open' if no audits are found

            # Add the calculated status to the current row
            row_dict = row.to_dict()
            row_dict['Status'] = status
            final_report_data.append(row_dict)

        print(f"Server Log: Successfully fetched and processed {len(final_report_data)} records for regular audit.")
        return final_report_data
        
    except Exception as e:
        print(f"Error fetching regular audit data: {e}")
        traceback.print_exc()
        return []
