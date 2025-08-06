import pandas as pd
import os
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pymysql

# Import common utilities from db_common.py, including get_data_from_mysql
from db_common import (
    get_db_connection, AGING_BASE_DIR, SVACC_BASE_DIR, TRNM_BASE_DIR,
    format_currency_py, normalize_cid_py, _clean_numeric_string_for_conversion,
    get_latest_data_for_month, get_data_from_mysql
)


# Mapping from GROUP code (from AGING CSV) to LOAN PRODUCT GROUP
LOAN_PRODUCT_GROUP_MAP = {
    "1": "Additional Loan", "2": "Agricultural Loan", "3": "Business Recovery Loan",
    "4": "Commercial Loan", "5": "Financing Loan - Vehicle", "6": "Financing Loan - Motorcycle",
    "7": "Real Estate Loan", "8": "Receivable Financing", "9": "SME", "10": "Instant Loan",
    "11": "Loan Against PS", "12": "Loan Against TD", "13": "Micro-Enterprise Loan",
    "14": "Pension Loan", "15": "Petty Cash Loan", "16": "Providential Loan",
    "17": "Restructured Loan", "18": "Salary Loan", "19": "Salary Loan Plus",
    "20": "Show Money Loan", "21": "Spcl Prep - Clothing", "22": "Spcl Prep - PEI",
    "23": "Spcl Prep - Salary Bonus", "24": "Allotment Loan", "25": "Others",
    "26": "Check Discounting", "27": "Rice Loan", "28": "FASS Loan",
    "29": "Restructured - Real Estate", "30": "Restructured - Agriculture",
    "31": "Restructured - FASS loan", "32": "Restructured - Commercial",
    "33": "Restructured - Providential", "34": "Restructured - Petty Cash",
    "35": "Restructured - Salary Loan", "36": "Restructured - Special Loan",
    "37": "Restructured - SME", "38": "Restructured - Others"
}

# Mapping SVACC ACCNAMEs to Report Headers (for Deposits section of Member-Borrowers)
DEPOSIT_ACCNAME_TO_REPORT_COL = {
    'Regular Savings': 'DEPOSITS_REGULAR_SAVINGS',
    'Share Capital': 'DEPOSITS_SHARE_CAPITAL',
    'ATM Savings': 'DEPOSITS_ATM',
    'Compulsory Savings Deposit': 'DEPOSITS_CSD',
    'Time Deposit -A': 'TIME_DEPOSITS_BALANCE',
    'Time Deposit -B': 'TIME_DEPOSITS_BALANCE',
    'Time Deposit -C': 'TIME_DEPOSITS_BALANCE',
    'Time Deposit - Maturity': 'TIME_DEPOSITS_BALANCE',
    'Time Deposit - Monthly': 'TIME_DEPOSITS_BALANCE',
}

def parse_dates_robustly(series, filename="unknown_file"):
    """
    Attempts to parse a pandas Series into datetime objects using multiple formats.
    It tries specific formats first, then falls back to general inference.
    Includes logging for diagnosis.
    """
    initial_count = len(series)
    
    # Attempt 1: Specific format with time and AM/PM
    parsed_dates = pd.to_datetime(series, errors='coerce', format='%m/%d/%Y %I:%M:%S %p')
    parsed_count_1 = parsed_dates.count()
    print(f"Server Log: ({filename}) Attempt 1 (mm/dd/yyyy hh:mm:ss am/pm): Successfully parsed {parsed_count_1} of {initial_count} dates.")
    
    # Attempt 2: Simpler MM/DD/YYYY format for unparsed dates
    unparsed_mask_1 = parsed_dates.isna()
    if unparsed_mask_1.any():
        remaining_to_parse_2 = series[unparsed_mask_1]
        parsed_dates[unparsed_mask_1] = pd.to_datetime(remaining_to_parse_2, errors='coerce', format='%m/%d/%Y')
        parsed_count_2 = parsed_dates.count() - parsed_count_1
        print(f"Server Log: ({filename}) Attempt 2 (mm/dd/yyyy): Successfully parsed {parsed_count_2} of {len(remaining_to_parse_2)} remaining dates.")
        
    # Attempt 3: YYYY-MM-DD format for any remaining unparsed dates
    unparsed_mask_2 = parsed_dates.isna()
    if unparsed_mask_2.any():
        remaining_to_parse_3 = series[unparsed_mask_2]
        parsed_dates[unparsed_mask_2] = pd.to_datetime(remaining_to_parse_3, errors='coerce', format='%Y-%m-%d')
        parsed_count_3 = parsed_dates.count() - (parsed_count_1 + parsed_count_2)
        print(f"Server Log: ({filename}) Attempt 3 (yyyy-mm-dd): Successfully parsed {parsed_count_3} of {len(remaining_to_parse_3)} remaining dates.")

    # Attempt 4: General inference for any remaining unparsed dates (without infer_datetime_format=True)
    unparsed_mask_3 = parsed_dates.isna()
    if unparsed_mask_3.any():
        remaining_to_parse_4 = series[unparsed_mask_3]
        parsed_dates[unparsed_mask_3] = pd.to_datetime(remaining_to_parse_4, errors='coerce', dayfirst=False, yearfirst=False)
        parsed_count_4 = parsed_dates.count() - (parsed_count_1 + parsed_count_2 + parsed_count_3)
        print(f"Server Log: ({filename}) Attempt 4 (General Inference): Successfully parsed {parsed_count_4} of {len(remaining_to_parse_4)} remaining dates.")
        
    final_unparsed_count = parsed_dates.isna().sum()
    if final_unparsed_count > 0:
        # Log a sample of unparsed values if they exist
        sample_unparsed = series[parsed_dates.isna()].head(5).tolist()
        print(f"Server Log: ({filename}) Warning: {final_unparsed_count} dates could not be parsed. Sample: {sample_unparsed}")
        
    return parsed_dates

def generate_deposit_counterpart_report_logic(branches, report_date_str, deposit_requirements_data, selected_report_entity):
    """
    Generates the Deposit Counterpart Report, including Member-Borrowers summary
    and detailed transaction listings, based on selected criteria and
    deposit requirements.
    """
    # Parse report_date_str to get target_date_dt
    try:
        target_date_dt = datetime.strptime(report_date_str, '%m/%d/%Y')
    except ValueError as e:
        print(f"Server Log: Error parsing report_date_str '{report_date_str}': {e}")
        return {
            "message": "Invalid date format provided. Please use MM/DD/YYYY.",
            "details_data": [],
            "member_borrowers_data": []
        }

    print(f"Server Log: Generating Deposit Counterpart Report for branches={branches}, date={report_date_str}, entity={selected_report_entity}.")

    member_borrowers_data = []
    details_data = []
    
    all_aging_dfs = []
    all_svacc_dfs = []

    # Fetch aging data for all selected branches
    if branches:
        # MODIFIED: Changed to named parameter for SQLAlchemy compatibility
        aging_query = "SELECT * FROM aging_report_data WHERE Branch IN :branches"
        all_aging_df = get_data_from_mysql(aging_query, params={"branches": branches})
        
        if all_aging_df.empty:
            print(f"Server Log: No AGING loan data found in MySQL for branches {branches}.")
            all_aging_df = pd.DataFrame(columns=[
                'Loan_Account', 'Name_of_Member', 'CID', 'Principal', 'Balance',
                'Disbursement_Date', 'Due_Date', 'Aging', 'Product', 'Group', 'Date', 'Branch'
            ])
            for col in ['Principal', 'Balance']: all_aging_df[col] = 0.0
            for col in ['Date', 'Disbursement_Date', 'Due_Date']: all_aging_df[col] = pd.to_datetime(all_aging_df[col])
        else:
            all_aging_df.columns = [col.replace('_', ' ').upper() for col in all_aging_df.columns]
            all_aging_df.rename(columns={'LOAN ACCOUNT': 'LOAN ACCT.', 'NAME OF MEMBER': 'NAME OF MEMBER', 
                                         'DISBURSEMENT DATE': 'DISBDATE', 'DUE DATE': 'DUE DATE'}, inplace=True)
            for col in ['PRINCIPAL', 'BALANCE']: all_aging_df[col] = pd.to_numeric(all_aging_df[col], errors='coerce').fillna(0)
            # Ensure 'DATE' column is parsed robustly
            all_aging_df['DATE'] = parse_dates_robustly(all_aging_df['DATE'], filename="aging_report_data")
            all_aging_df['DISBDATE'] = parse_dates_robustly(all_aging_df['DISBDATE'], filename="aging_report_data_disbdate")
            all_aging_df['DUE DATE'] = parse_dates_robustly(all_aging_df['DUE DATE'], filename="aging_report_data_duedate")

            if 'CID' in all_aging_df.columns: all_aging_df['CID_NORM'] = all_aging_df['CID'].apply(normalize_cid_py)
            else: all_aging_df['CID_NORM'] = ''
            print(f"Server Log: Loaded {len(all_aging_df)} loan records from MySQL aging_report_data for branches {branches}.")
    else:
        print("Server Log: No branches provided for AGING data query.")
        all_aging_df = pd.DataFrame(columns=[
            'Loan_Account', 'Name_of_Member', 'CID', 'Principal', 'Balance',
            'Disbursement_Date', 'Due_Date', 'Aging', 'Product', 'Group', 'Date', 'Branch'
        ])
        for col in ['Principal', 'Balance']: all_aging_df[col] = 0.0
        for col in ['Date', 'Disbursement_Date', 'Due_Date']: all_aging_df[col] = pd.to_datetime(all_aging_df[col])


    # Fetch SVACC data for all selected branches
    if branches:
        for branch_name in branches:
            sanitized_branch_name_for_table = branch_name.lower().replace(' ', '_')
            svacc_table_name = f"svacc_{sanitized_branch_name_for_table}"
            svacc_query = f"SELECT * FROM `{svacc_table_name}`"
            
            df_svacc_branch = get_data_from_mysql(svacc_query)
            
            if df_svacc_branch.empty:
                print(f"Server Log: No SVACC deposit data found in MySQL table '{svacc_table_name}'.")
            else:
                df_svacc_branch.columns = [col.upper() for col in df_svacc_branch.columns]
                for col in ['BAL', 'INTRATE', 'CUMINTPD', 'CUMTAXW']:
                    df_svacc_branch[col] = pd.to_numeric(df_svacc_branch[col], errors='coerce').fillna(0)
                # Ensure 'DOPEN' column is parsed robustly
                df_svacc_branch['DOPEN'] = parse_dates_robustly(df_svacc_branch['DOPEN'], filename=f"svacc_{branch_name}")
                df_svacc_branch['DOLASTTRN'] = parse_dates_robustly(df_svacc_branch['DOLASTTRN'], filename=f"svacc_{branch_name}_dolasttrn")
                df_svacc_branch['MATDATE'] = parse_dates_robustly(df_svacc_branch['MATDATE'], filename=f"svacc_{branch_name}_matdate")

                if 'CID' in df_svacc_branch.columns: df_svacc_branch['CID_NORM'] = df_svacc_branch['CID'].apply(normalize_cid_py)
                else: df_svacc_branch['CID_NORM'] = ''
                all_svacc_dfs.append(df_svacc_branch)
                print(f"Server Log: Loaded {len(df_svacc_branch)} deposit records from MySQL table '{svacc_table_name}'.")
        
        if all_svacc_dfs:
            all_svacc_df = pd.concat(all_svacc_dfs, ignore_index=True)
        else:
            print("Server Log: No SVACC data collected for any selected branch.")
            all_svacc_df = pd.DataFrame(columns=[
                'ACC', 'CID', 'TYPE', 'BAL', 'ACCNAME', 'DOPEN', 'INTRATE', 'GLCODE',
                'DOLASTTRN', 'MATDATE', 'CUMINTPD', 'CUMTAXW', 'Branch'
            ])
            for col in ['BAL', 'INTRATE', 'CUMINTPD', 'CUMTAXW']: all_svacc_df[col] = 0.0
            for col in ['DOPEN', 'DOLASTTRN', 'MATDATE']: all_svacc_df[col] = pd.to_datetime(all_svacc_df[col])
            all_svacc_df['CID_NORM'] = ''
    else:
        print("Server Log: No branches provided for SVACC data query.")
        all_svacc_df = pd.DataFrame(columns=[
            'ACC', 'CID', 'TYPE', 'BAL', 'ACCNAME', 'DOPEN', 'INTRATE', 'GLCODE',
            'DOLASTTRN', 'MATDATE', 'CUMINTPD', 'CUMTAXW', 'Branch'
        ])
        for col in ['BAL', 'INTRATE', 'CUMINTPD', 'CUMTAXW']: all_svacc_df[col] = 0.0
        for col in ['DOPEN', 'DOLASTTRN', 'MATDATE']: all_svacc_df[col] = pd.to_datetime(all_svacc_df[col])
        all_svacc_df['CID_NORM'] = ''
    
    
    # Check for NaT values in the DATE column before passing to get_latest_data_for_month
    if not all_aging_df.empty:
        nat_count_aging = all_aging_df['DATE'].isna().sum()
        if nat_count_aging > 0:
            print(f"Server Log: Found {nat_count_aging} NaT (Not a Time) values in 'DATE' column of AGING data from DB.")

    if not all_svacc_df.empty:
        nat_count_svacc = all_svacc_df['DOPEN'].isna().sum()
        if nat_count_svacc > 0:
            print(f"Server Log: Found {nat_count_svacc} NaT (Not a Time) values in 'DOPEN' column of SVACC data from DB.")


    # Use the parsed target_date_dt directly for loans (aging_report_data)
    loans_in_period_df = get_latest_data_for_month(all_aging_df, 'DATE', target_date_dt, 'LOAN ACCT.')
    
    # MODIFIED: SVACC data should NOT be filtered by date, as per user's clarification.
    # Use all available SVACC data for the selected branches.
    deposits_in_period_df = all_svacc_df.copy()
    print(f"Server Log: SVACC data used without date filtering. deposits_in_period_df shape: {deposits_in_period_df.shape}")

    deposit_req_lookup = {req['product']: req for req in deposit_requirements_data}


    if not loans_in_period_df.empty:
        def calculate_dc_fields_vectorized(row):
            product = row['PRODUCT']
            group_code_aging = str(row.get('GROUP', '')).strip()
            loan_product_group_for_req = LOAN_PRODUCT_GROUP_MAP.get(group_code_aging, product)
            
            matching_req = deposit_req_lookup.get(loan_product_group_for_req)

            dc_conditions_str = ""
            dc_req_value = 0.0

            if matching_req:
                condition = matching_req['condition']
                dc_config = matching_req['depositCounterpart']
                
                dc_conditions_str = f"{condition}"
                if condition == "% of Total Deposit":
                    if 'percentage' in dc_config: dc_conditions_str += f" ({format_currency_py(dc_config['percentage'])}%)"
                    if 'depositType' in dc_config: dc_conditions_str += f" of {dc_config['depositType']}"
                elif condition == "% of Loan Principal":
                    if 'percentage' in dc_config: dc_conditions_str += f" ({format_currency_py(dc_config['percentage'])}%)"
                elif condition == "Specific Amount per Deposit":
                    if 'shareAmount' in dc_config: dc_conditions_str += f" (Share: {format_currency_py(dc_config['shareAmount'])})"
                    if 'savingsAmount' in dc_config: dc_conditions_str += f" (Savings: {format_currency_py(dc_config['savingsAmount'])})"
                elif condition == "Number of Times in Principal":
                    if 'numberOfTimes' in dc_config: dc_conditions_str += f" ({format_currency_py(dc_config['numberOfTimes'])}x)"

                if condition == "% of Total Deposit":
                    # Check if dc_config['depositType'] is 'Share Capital' or 'Regular Savings'
                    # and use the corresponding deposit balance. Otherwise, use total deposits.
                    deposit_type = dc_config.get('depositType')
                    if deposit_type == 'Share Capital':
                        deposit_balance = row.get('DEPOSITS_SHARE_CAPITAL', 0)
                    elif deposit_type == 'Savings Deposit': # Changed from 'Regular Savings' to 'Savings Deposit' to match frontend option
                        deposit_balance = row.get('DEPOSITS_REGULAR_SAVINGS', 0)
                    else: # Default to total deposits if type not specified or recognized ('All Deposits')
                        deposit_balance = row.get('DEPOSITS_TOTAL', 0)

                    if 'percentage' in dc_config:
                        dc_req_value = (deposit_balance * (dc_config['percentage'] / 100))

                elif condition == "% of Loan Principal":
                    if 'percentage' in dc_config:
                        dc_req_value = (row['BALANCE'] * (dc_config['percentage'] / 100))
                elif condition == "Specific Amount per Deposit":
                    dc_req_value = (dc_config.get('shareAmount', 0) + dc_config.get('savingsAmount', 0))
                elif condition == "Number of Times in Principal":
                    dc_req_value = (row['BALANCE'] * dc_config.get('numberOfTimes', 0))
            
            return pd.Series([dc_conditions_str, dc_req_value])

        loans_in_period_df['DC_CONDITIONS'] = ''
        loans_in_period_df['DC_REQ'] = 0.0
        loans_in_period_df[['DC_CONDITIONS', 'DC_REQ']] = loans_in_period_df.apply(calculate_dc_fields_vectorized, axis=1)

        details_df = loans_in_period_df.copy()
        details_df['NAME'] = details_df['NAME OF MEMBER']
        details_df['DISBURSED'] = details_df['DISBDATE'].dt.strftime('%m/%d/%Y').fillna('')
        details_df['MATURITY'] = details_df['DUE DATE'].dt.strftime('%m/%d/%Y').fillna('')
        details_df['ACCOUNT'] = details_df['LOAN ACCT.']

        # Ensure numeric columns are filled before formatting and conversion
        details_df['PRINCIPAL'] = details_df['PRINCIPAL'].fillna(0)
        details_df['BALANCE'] = details_df['BALANCE'].fillna(0)
        details_df['DC_REQ'] = details_df['DC_REQ'].fillna(0)

        details_df['PRINCIPAL_FORMATTED'] = details_df['PRINCIPAL'].apply(format_currency_py)
        details_df['BALANCE_FORMATTED'] = details_df['BALANCE'].apply(format_currency_py)
        details_df['DC_REQ_FORMATTED'] = details_df['DC_REQ'].apply(format_currency_py)

        details_data = details_df[[
            'NAME', 'CID_NORM', 'ACCOUNT', 'PRINCIPAL_FORMATTED', 'BALANCE_FORMATTED',
            'DISBURSED', 'MATURITY', 'PRODUCT', 'AGING', 'DC_CONDITIONS', 'DC_REQ_FORMATTED', 'GROUP',
            'PRINCIPAL', 'BALANCE', 'DC_REQ'
        ]].rename(columns={
            'CID_NORM': 'CID',
            'PRINCIPAL_FORMATTED': 'PRINCIPAL',
            'BALANCE_FORMATTED': 'BALANCE',
            'DC_REQ_FORMATTED': 'DC_REQ'
        }).to_dict(orient='records')

        print(f"Server Log: Generated {len(details_data)} detailed loan entries.")
    else:
        print("Server Log: No Details data generated.")
        details_df = pd.DataFrame(columns=[
            'NAME', 'CID', 'ACCOUNT', 'PRINCIPAL', 'BALANCE', 'DISBURSED', 
            'MATURITY', 'PRODUCT', 'AGING', 'DC_CONDITIONS', 'DC_REQ', 'GROUP', 'CID_NORM'
        ])
        for col in ['PRINCIPAL', 'BALANCE', 'DC_REQ']:
            details_df[col] = 0.0


    member_borrowers_final_data = []

    all_cids_in_scope = pd.Series(dtype=str)
    if not loans_in_period_df.empty:
        all_cids_in_scope = pd.concat([all_cids_in_scope, loans_in_period_df['CID_NORM']])
    if not deposits_in_period_df.empty:
        all_cids_in_scope = pd.concat([all_cids_in_scope, deposits_in_period_df['CID_NORM']])
    all_cids_in_scope = all_cids_in_scope.dropna().unique()
    all_cids_in_scope = [cid for cid in all_cids_in_scope if cid and cid != '']

    if not details_df.empty:
        # Ensure 'GROUP' column is string type for comparison
        details_df['GROUP'] = details_df['GROUP'].astype(str)

        loans_grouped_by_cid = details_df.groupby('CID').agg(
            LOANS_PRINCIPAL=('PRINCIPAL', 'sum'),
            LOANS_CURRENT_BALANCE=('BALANCE', lambda x: x[details_df.loc[x.index, 'AGING'].str.upper() == 'NOT YET DUE'].sum()),
            LOANS_PAST_DUE_BALANCE=('BALANCE', lambda x: x[details_df.loc[x.index, 'AGING'].str.upper() != 'NOT YET DUE'].sum()),
            TOTAL_DC_REQ=('DC_REQ', lambda x: x[~details_df.loc[x.index, 'GROUP'].isin(['11', '12'])].sum()),
            TOTAL_TDC_REQ=('DC_REQ', lambda x: x[details_df.loc[x.index, 'GROUP'].isin(['11', '12'])].sum()),
            NAME_LOAN=('NAME', 'first'),
            ACCOUNTS_COUNT_LOAN=('ACCOUNT', 'count')
        ).reset_index()
        loans_grouped_by_cid['LOANS_TOTAL_BALANCE'] = loans_grouped_by_cid['LOANS_CURRENT_BALANCE'] + loans_grouped_by_cid['LOANS_PAST_DUE_BALANCE']
        
        for col in ['LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE', 'TOTAL_DC_REQ', 'TOTAL_TDC_REQ', 'ACCOUNTS_COUNT_LOAN']:
            loans_grouped_by_cid[col] = pd.to_numeric(loans_grouped_by_cid[col], errors='coerce').fillna(0)
    else:
        loans_grouped_by_cid = pd.DataFrame(columns=['CID', 'NAME_LOAN', 'LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE', 'TOTAL_DC_REQ', 'TOTAL_TDC_REQ', 'ACCOUNTS_COUNT_LOAN'])
        for col in ['LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE', 'TOTAL_DC_REQ', 'TOTAL_TDC_REQ', 'ACCOUNTS_COUNT_LOAN']:
            loans_grouped_by_cid[col] = 0.0

    if not deposits_in_period_df.empty:
        deposits_in_period_df['DEP_CATEGORY'] = deposits_in_period_df['ACCNAME'].apply(
            lambda x: next((col for accname, col in DEPOSIT_ACCNAME_TO_REPORT_COL.items() if x == accname), None)
        )
        deposits_in_period_df_mapped = deposits_in_period_df.dropna(subset=['DEP_CATEGORY']).copy()

        deposit_sums_by_cid_category = deposits_in_period_df_mapped.groupby(['CID_NORM', 'DEP_CATEGORY'])['BAL'].sum().unstack(fill_value=0)
        
        for col_name in DEPOSIT_ACCNAME_TO_REPORT_COL.values():
            if col_name not in deposit_sums_by_cid_category.columns:
                deposit_sums_by_cid_category[col_name] = 0.0

        deposits_grouped_by_cid = deposit_sums_by_cid_category.reset_index().rename(columns={'CID_NORM': 'CID'})
        deposits_grouped_by_cid['DEPOSITS_TOTAL'] = deposits_grouped_by_cid[[col for col in DEPOSIT_ACCNAME_TO_REPORT_COL.values() if col != 'TIME_DEPOSITS_BALANCE']].sum(axis=1) + deposits_grouped_by_cid['TIME_DEPOSITS_BALANCE']
        
        # Ensure 'NAME_DEP' is handled if it doesn't exist
        if 'NAME_DEP' not in deposits_grouped_by_cid.columns:
            # Safely get a name from the original deposits_in_period_df if available
            name_mapping = deposits_in_period_df_mapped.set_index('CID_NORM')['ACCNAME'].to_dict()
            deposits_grouped_by_cid['NAME_DEP'] = deposits_grouped_by_cid['CID'].map(name_mapping).fillna('')
        if 'ACCOUNTS_COUNT_DEP' not in deposits_grouped_by_cid.columns:
            deposits_grouped_by_cid['ACCOUNTS_COUNT_DEP'] = deposits_in_period_df_mapped.groupby('CID_NORM')['ACC'].count().reset_index(name='ACCOUNTS_COUNT_DEP')['ACCOUNTS_COUNT_DEP']
        
        for col in [col for col in DEPOSIT_ACCNAME_TO_REPORT_COL.values()] + ['DEPOSITS_TOTAL', 'ACCOUNTS_COUNT_DEP']:
            deposits_grouped_by_cid[col] = pd.to_numeric(deposits_grouped_by_cid[col], errors='coerce').fillna(0)
    else:
        deposits_grouped_by_cid = pd.DataFrame(columns=['CID'] + list(DEPOSIT_ACCNAME_TO_REPORT_COL.values()) + ['DEPOSITS_TOTAL', 'NAME_DEP', 'ACCOUNTS_COUNT_DEP'])
        for col in deposits_grouped_by_cid.columns:
            if col != 'CID' and col != 'NAME_DEP':
                deposits_grouped_by_cid[col] = 0.0


    merged_data = pd.merge(
        loans_grouped_by_cid,
        deposits_grouped_by_cid,
        on='CID',
        how='outer',
        suffixes=('_loan', '_dep')
    )

    all_numeric_cols_from_groups = list(loans_grouped_by_cid.select_dtypes(include='number').columns) + \
                                   list(deposits_grouped_by_cid.select_dtypes(include='number').columns)
    
    numeric_cols_to_fill_after_merge = [col for col in set(all_numeric_cols_from_groups) if col != 'CID']

    for col in numeric_cols_to_fill_after_merge:
        # Check if the column exists in merged_data before attempting to convert
        if col in merged_data.columns:
            merged_data[col] = pd.to_numeric(merged_data[col], errors='coerce').fillna(0)
        # Handle _loan and _dep suffixes if they were not merged into a single column
        if f'{col}_loan' in merged_data.columns:
            merged_data[f'{col}_loan'] = pd.to_numeric(merged_data[f'{col}_loan'], errors='coerce').fillna(0)
        if f'{col}_dep' in merged_data.columns:
            merged_data[f'{col}_dep'] = pd.to_numeric(merged_data[f'{col}_dep'], errors='coerce').fillna(0)


    merged_data['NAME'] = merged_data['NAME_LOAN'].fillna(merged_data['NAME_DEP']).fillna('')

    merged_data['BRANCH'] = selected_report_entity # Assign the original selected entity (branch or area)

    # Ensure ACCOUNTS_COUNT is numeric and filled with 0
    merged_data['ACCOUNTS_COUNT_LOAN'] = merged_data['ACCOUNTS_COUNT_LOAN'].fillna(0)
    merged_data['ACCOUNTS_COUNT_DEP'] = merged_data['ACCOUNTS_COUNT_DEP'].fillna(0)
    merged_data['ACCOUNTS_COUNT'] = merged_data['ACCOUNTS_COUNT_LOAN'] + merged_data['ACCOUNTS_COUNT_DEP']


    # Convert TOTAL_DC_REQ and TOTAL_TDC_REQ to numeric before division
    merged_data['TOTAL_DC_REQ'] = pd.to_numeric(merged_data['TOTAL_DC_REQ'], errors='coerce').fillna(0)
    merged_data['TOTAL_TDC_REQ'] = pd.to_numeric(merged_data['TOTAL_TDC_REQ'], errors='coerce').fillna(0)

    # Ensure DEPOSITS_TOTAL and TIME_DEPOSITS_BALANCE are numeric before division
    merged_data['DEPOSITS_TOTAL'] = pd.to_numeric(merged_data['DEPOSITS_TOTAL'], errors='coerce').fillna(0)
    merged_data['TIME_DEPOSITS_BALANCE'] = pd.to_numeric(merged_data['TIME_DEPOSITS_BALANCE'], errors='coerce').fillna(0)


    # Calculate compliance and handle division by zero and inf/-inf
    merged_data['DC_COMPLIANCE'] = (merged_data['DEPOSITS_TOTAL'] / merged_data['TOTAL_DC_REQ'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0.0)
    merged_data['TDC_COMPLIANCE'] = (merged_data['TIME_DEPOSITS_BALANCE'] / merged_data['TOTAL_TDC_REQ'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0.0)

    final_member_borrowers_cols = [
        'CID', 'NAME', 'BRANCH', 
        'LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE',
        'DEPOSITS_REGULAR_SAVINGS', 'DEPOSITS_SHARE_CAPITAL', 'DEPOSITS_ATM', 'DEPOSITS_CSD', 'DEPOSITS_TOTAL',
        'TOTAL_DC', 'TIME_DEPOSITS_BALANCE', 'TOTAL_TDC', 'DC_COMPLIANCE', 'TDC_COMPLIANCE', 'ACCOUNTS_COUNT'
    ]

    # Assign calculated TOTAL_DC_REQ and TOTAL_TDC_REQ to the final column names
    merged_data['TOTAL_DC'] = merged_data['TOTAL_DC_REQ']
    merged_data['TOTAL_TDC'] = merged_data['TOTAL_TDC_REQ']

    for col in final_member_borrowers_cols:
        if col not in merged_data.columns:
            if col in ['LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE',
                       'DEPOSITS_REGULAR_SAVINGS', 'DEPOSITS_SHARE_CAPITAL', 'DEPOSITS_ATM', 'DEPOSITS_CSD', 'DEPOSITS_TOTAL',
                       'TOTAL_DC', 'TIME_DEPOSITS_BALANCE', 'TOTAL_TDC', 'DC_COMPLIANCE', 'TDC_COMPLIANCE', 'ACCOUNTS_COUNT']:
                merged_data[col] = 0.0
            else:
                merged_data[col] = ''
        
        # Ensure that all final numeric columns are indeed numeric and filled with 0 before conversion
        if col in ['LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE',
                   'DEPOSITS_REGULAR_SAVINGS', 'DEPOSITS_SHARE_CAPITAL', 'DEPOSITS_ATM', 'DEPOSITS_CSD', 'DEPOSITS_TOTAL',
                   'TOTAL_DC', 'TIME_DEPOSITS_BALANCE', 'TOTAL_TDC', 'DC_COMPLIANCE', 'TDC_COMPLIANCE', 'ACCOUNTS_COUNT']:
            merged_data[col] = pd.to_numeric(merged_data[col], errors='coerce').fillna(0)


    member_borrowers_result_df = merged_data[final_member_borrowers_cols].copy()
    
    member_borrowers_result_df['LOANS_PRINCIPAL_FORMATTED'] = member_borrowers_result_df['LOANS_PRINCIPAL'].apply(format_currency_py)
    member_borrowers_result_df['LOANS_CURRENT_BALANCE_FORMATTED'] = member_borrowers_result_df['LOANS_CURRENT_BALANCE'].apply(format_currency_py)
    member_borrowers_result_df['LOANS_PAST_DUE_BALANCE_FORMATTED'] = member_borrowers_result_df['LOANS_PAST_DUE_BALANCE'].apply(format_currency_py)
    member_borrowers_result_df['LOANS_TOTAL_BALANCE_FORMATTED'] = member_borrowers_result_df['LOANS_TOTAL_BALANCE'].apply(format_currency_py)
    member_borrowers_result_df['DEPOSITS_REGULAR_SAVINGS_FORMATTED'] = member_borrowers_result_df['DEPOSITS_REGULAR_SAVINGS'].apply(format_currency_py)
    member_borrowers_result_df['DEPOSITS_SHARE_CAPITAL_FORMATTED'] = member_borrowers_result_df['DEPOSITS_SHARE_CAPITAL'].apply(format_currency_py)
    member_borrowers_result_df['DEPOSITS_ATM_FORMATTED'] = member_borrowers_result_df['DEPOSITS_ATM'].apply(format_currency_py)
    member_borrowers_result_df['DEPOSITS_CSD_FORMATTED'] = member_borrowers_result_df['DEPOSITS_CSD'].apply(format_currency_py)
    member_borrowers_result_df['DEPOSITS_TOTAL_FORMATTED'] = member_borrowers_result_df['DEPOSITS_TOTAL'].apply(format_currency_py)
    member_borrowers_result_df['TOTAL_DC_FORMATTED'] = member_borrowers_result_df['TOTAL_DC'].apply(format_currency_py)
    member_borrowers_result_df['TIME_DEPOSITS_BALANCE_FORMATTED'] = member_borrowers_result_df['TIME_DEPOSITS_BALANCE'].apply(format_currency_py)
    member_borrowers_result_df['TOTAL_TDC_FORMATTED'] = member_borrowers_result_df['TOTAL_TDC'].apply(format_currency_py)

    member_borrowers_final_data = member_borrowers_result_df.to_dict(orient='records')
        
    for row in member_borrowers_final_data:
        row['DC_COMPLIANCE'] = row['DC_COMPLIANCE'] if pd.notna(row['DC_COMPLIANCE']) else 0.0
        row['TDC_COMPLIANCE'] = row['TDC_COMPLIANCE'] if pd.notna(row['TDC_COMPLIANCE']) else 0.0
        row['ACCOUNTS_COUNT'] = int(row['ACCOUNTS_COUNT']) if pd.notna(row['ACCOUNTS_COUNT']) else 0

    if not member_borrowers_result_df.empty:
        member_borrowers_result_df.sort_values(by='LOANS_TOTAL_BALANCE', ascending=False, inplace=True)
        member_borrowers_data = member_borrowers_result_df.to_dict(orient='records')
        print(f"Server Log: Generated {len(member_borrowers_data)} member-borrowers entries.")
    else:
        print("Server Log: No Member-Borrowers data generated.")

    return {
        "message": "Deposit Counterpart Report generated successfully!",
        "details_data": details_data,
        "member_borrowers_data": member_borrowers_data
    }

# Removed all Deposit Liabilities, Maturity, and Interest Rate related functions
# These have been moved to operations_dl.py

