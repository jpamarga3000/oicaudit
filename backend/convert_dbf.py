# convert_dbf.py
import os
import csv
from dbfread import DBF # Make sure you have dbfread installed: pip install dbfread

def process_dbf_to_csv_web(input_dir, output_dir):
    """
    Converts all DBF files in the input_dir to CSV files in the output_dir.
    Attempts multiple encodings for DBF reading.

    Args:
        input_dir (str): The directory containing the DBF files.
        output_dir (str): The directory where the CSV files will be saved.
    
    Returns:
        str: The path to the output_dir, regardless of whether single or multiple files were converted.
             Raises an exception if no files are found or conversion fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"Server Log (Convert DBF): Starting DBF to CSV conversion from {input_dir} to {output_dir}")

    encodings_to_try = ['latin1', 'cp1252', 'utf-8', 'iso-8859-2']
    dbf_files_found = False
    converted_count = 0
    
    # List to store paths of successfully converted CSVs within output_dir
    converted_csv_paths = [] 

    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith('.dbf') and not file_name.startswith('~'):
            dbf_files_found = True
            dbf_path = os.path.join(input_dir, file_name)
            csv_file_name = os.path.splitext(file_name)[0] + '.csv'
            csv_path = os.path.join(output_dir, csv_file_name)

            print(f'Server Log (Convert DBF): 🔄 Converting {file_name}...')

            try:
                success = False
                for encoding in encodings_to_try:
                    try:
                        table = DBF(dbf_path, load=True, encoding=encoding, ignore_missing_memofile=True)
                        
                        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerow(table.field_names) # Write header row
                            for record in table:
                                try:
                                    writer.writerow(list(record.values()))
                                except Exception as e:
                                    print(f'Server Log (Convert DBF): ⚠️ Skipping corrupted record in {file_name}: {e}')
                        
                        print(f'Server Log (Convert DBF): ✅ Converted {file_name} using encoding: {encoding}')
                        success = True
                        converted_count += 1
                        converted_csv_paths.append(csv_path) # Add to list of converted paths
                        break # Break from encoding loop if successful
                    except UnicodeDecodeError as e:
                        print(f'Server Log (Convert DBF): ⚠️ Encoding {encoding} failed for {file_name}: {e}')
                    except Exception as e:
                        print(f'Server Log (Convert DBF): ⚠️ Failed on encoding {encoding} for {file_name}: {e}')
                
                if not success:
                    raise Exception(f'Could not decode {file_name} with known encodings.')

            except Exception as e:
                print(f'Server Log (Convert DBF): ❌ Failed to convert {file_name}: {e}')
                raise Exception(f"Failed to convert {file_name}: {e}")

    if not dbf_files_found:
        raise Exception("No DBF files found in the specified input directory.")
    
    if converted_count == 0 and dbf_files_found:
        raise Exception("No DBF files were successfully converted.")

    print("Server Log (Convert DBF): 🎉 All conversions attempted. Check 'CSV_Output' folder for results.")
    
    # Always return the output_dir, as it will contain all converted files
    return output_dir
