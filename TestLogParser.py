import os
import pandas as pd
import re
import shutil # For clearing dummy directories

# --- GLOBAL LOGGING CONFIGURATION ---
# Define log levels as constants for clarity
LOG_LEVEL_NONE = 0
LOG_LEVEL_ERROR = 1
LOG_LEVEL_WARNING = 2
LOG_LEVEL_INFO = 3
LOG_LEVEL_DEBUG = 4

# Global variable to hold the current log level, initialized by the main function
_SCRIPT_LOG_LEVEL = LOG_LEVEL_INFO # Default to INFO level if not explicitly set

def _log_message(level, message):
    """
    Prints a log message if the message's level is less than or equal to
    the script's current global log level.

    Args:
        level (int): The log level of this specific message (e.g., LOG_LEVEL_ERROR, LOG_LEVEL_INFO).
        message (str): The log message to print.
    """
    if _SCRIPT_LOG_LEVEL >= level:
        # Prepend level tag for better readability in logs
        if level == LOG_LEVEL_ERROR:
            prefix = "ERROR: "
        elif level == LOG_LEVEL_WARNING:
            prefix = "WARNING: "
        elif level == LOG_LEVEL_INFO:
            prefix = "INFO: "
        elif level == LOG_LEVEL_DEBUG:
            prefix = "DEBUG: "
        else:
            prefix = "" # No prefix for LOG_LEVEL_NONE or unexpected level
        print(f"{prefix}{message}")

def _parse_summary_section(file_path, config):
    """
    Parses the structured summary section from a test log file,
    extracting test case numbers and their results based on provided configuration.

    Args:
        file_path (str): The absolute path to the log file.
        config (dict): A dictionary containing configuration for parsing,
                       e.g., 'summary_section_start', 'test_no_header', 'test_result_header'.

    Returns:
        list: A list of dictionaries, where each dictionary contains the test number
              and result for a test case found in the summary section. Returns an empty list
              if the section is not found or parsing fails.
    """
    summary_data = []
    in_summary_section = False
    header_line_found = False
    awaiting_data_start = False 
    
    summary_section_start = config['summary_section_start']
    test_no_header = config['test_no_header']
    test_result_header = config['test_result_header']

    # Regex to capture test number and result.
    # Pattern: (\w+) captures alphanumeric IDs like "TC_0001" or "TID05".
    # \s*[-*]?\s*: Matches optional spaces and the optional '-' or '*' character.
    # (\w+): Matches the test result string (e.g., PASS, FAIL, SKIP).
    test_result_pattern = re.compile(r'^\s*(\w+)\s*[-*]?\s*(\w+)')

    _log_message(LOG_LEVEL_DEBUG, f"Parsing file: {file_path} with config: {config}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_stripped = line.strip()

                if not in_summary_section:
                    if summary_section_start in line_stripped:
                        in_summary_section = True
                        _log_message(LOG_LEVEL_DEBUG, f"Found '{summary_section_start}' in {file_path}. Entering summary section parsing.")
                    continue

                if not header_line_found:
                    # Check for both configured headers to identify the header line
                    if test_no_header in line_stripped and test_result_header in line_stripped:
                        header_line_found = True
                        awaiting_data_start = True
                        _log_message(LOG_LEVEL_DEBUG, f"Found header line in {file_path}: '{line_stripped}'. Now awaiting data/separator.")
                    continue 

                if awaiting_data_start:
                    # Allow for both '---' and '=====' as separator lines
                    if line_stripped.startswith('---') or line_stripped.startswith('=' * 5): 
                        _log_message(LOG_LEVEL_DEBUG, f"Skipping separator line in {file_path}: '{line_stripped}'. Ready for data.")
                        awaiting_data_start = False
                        continue
                    else:
                        awaiting_data_start = False

                # Stop parsing if we hit known footer lines or empty lines
                if line_stripped.startswith("Script End Time:") or \
                   line_stripped.startswith("Total Run Time:") or \
                   line_stripped == "": 
                    _log_message(LOG_LEVEL_DEBUG, f"Stopping parsing in {file_path} due to footer/empty line: '{line_stripped}'")
                    break

                match = test_result_pattern.match(line_stripped)
                if match:
                    test_no = match.group(1)
                    result = match.group(2)
                    # Use configurable headers as dictionary keys
                    summary_data.append({test_no_header: test_no, test_result_header: result})
                    _log_message(LOG_LEVEL_DEBUG, f"Parsed data from {file_path}: {test_no_header}='{test_no}', {test_result_header}='{result}' from line: '{line_stripped}'")
                else:
                    _log_message(LOG_LEVEL_DEBUG, f"Skipped non-matching line in {file_path}: '{line_stripped}'")
                            
    except FileNotFoundError:
        _log_message(LOG_LEVEL_WARNING, f"File not found - {file_path}")
    except Exception as e:
        _log_message(LOG_LEVEL_ERROR, f"Error parsing summary section in {file_path}: {e}")

    _log_message(LOG_LEVEL_DEBUG, f"Final summary_data for {file_path}: {summary_data}")
    return summary_data

def compare_test_summaries(previous_dir, current_dir, output_excel_file, config):
    """
    Compares test summary sections from log files in two hierarchical directories
    and generates a single Excel report of the differences.

    Args:
        previous_dir (str): The path to the root directory of previous test results.
        current_dir (str): The path to the root directory of current test results.
        output_excel_file (str): The name of the output Excel file.
        config (dict): A dictionary containing configuration for parsing.
    """
    
    if not os.path.isdir(previous_dir):
        _log_message(LOG_LEVEL_ERROR, f"Previous results directory not found: {previous_dir}")
        return
    if not os.path.isdir(current_dir):
        _log_message(LOG_LEVEL_ERROR, f"Current results directory not found: {current_dir}")
        return

    _log_message(LOG_LEVEL_INFO, f"Comparing previous results in: '{previous_dir}'")
    _log_message(LOG_LEVEL_INFO, f"With current results in:       '{current_dir}'")

    prev_files = {}  # {relative_path: absolute_path}
    current_files = {} # {relative_path: absolute_path}

    for root, _, files in os.walk(previous_dir):
        for file in files:
            if file.startswith('.'):
                _log_message(LOG_LEVEL_DEBUG, f"Skipping dotfile in previous: {file}")
                continue
            abs_path = os.path.join(root, file)
            relative_path = os.path.relpath(abs_path, previous_dir)
            prev_files[relative_path] = abs_path
    _log_message(LOG_LEVEL_INFO, f"\nPrevious files discovered: {prev_files}")

    for root, _, files in os.walk(current_dir):
        for file in files:
            if file.startswith('.'):
                _log_message(LOG_LEVEL_DEBUG, f"Skipping dotfile in current: {file}")
                continue
            abs_path = os.path.join(root, file)
            relative_path = os.path.relpath(abs_path, current_dir)
            current_files[relative_path] = abs_path
    _log_message(LOG_LEVEL_INFO, f"Current files discovered: {current_files}")

    all_unique_relative_paths = sorted(list(set(prev_files.keys()) | set(current_files.keys())))
    
    if not all_unique_relative_paths:
        _log_message(LOG_LEVEL_WARNING, "No log files found in either directory (excluding dotfiles). No report will be generated.")
        return

    all_comparison_rows = []

    _log_message(LOG_LEVEL_INFO, f"\nFound {len(all_unique_relative_paths)} unique files across both results to process.")

    for relative_path in all_unique_relative_paths:
        abs_curr_path = current_files.get(relative_path)
        abs_prev_path = prev_files.get(relative_path)

        _log_message(LOG_LEVEL_INFO, f"Processing file: {relative_path}")

        curr_summary_data = []
        if abs_curr_path:
            curr_summary_data = _parse_summary_section(abs_curr_path, config)
        else:
            _log_message(LOG_LEVEL_INFO, f"File '{relative_path}' not found in current results. Will treat as removed.")

        prev_summary_data = []
        if abs_prev_path:
            prev_summary_data = _parse_summary_section(abs_prev_path, config)
        else:
            _log_message(LOG_LEVEL_INFO, f"File '{relative_path}' not found in previous results. Will treat as new.")

        # Dynamically use configured headers as dictionary keys for mapping
        prev_map = {item[config['test_no_header']]: item[config['test_result_header']] for item in prev_summary_data}
        curr_map = {item[config['test_no_header']]: item[config['test_result_header']] for item in curr_summary_data}

        # Get all unique test numbers from both previous and current summaries for this file
        # The 'keys()' here will now be the values from config['test_no_header']
        all_test_nos = sorted(list(set(prev_map.keys()) | set(curr_map.keys())))

        dir_path = os.path.dirname(relative_path)
        filename = os.path.basename(relative_path)

        if not abs_prev_path and not abs_curr_path:
            _log_message(LOG_LEVEL_ERROR, f"ERROR: {relative_path} found in neither, this indicates a logic error in path collection.")
            continue
        elif not abs_prev_path: # File is new in current directory
            if not all_test_nos: # New file with no summary data
                all_comparison_rows.append({
                    "Path": dir_path,
                    "File": filename,
                    config['test_no_header']: "", 
                    "Previous Result": "",
                    "Current Result": "",
                    "Diff": "New File (No Summary Data)"
                })
            else: # New file with summary data
                for test_no in all_test_nos:
                    curr_result = curr_map.get(test_no, "")
                    all_comparison_rows.append({
                        "Path": dir_path,
                        "File": filename,
                        config['test_no_header']: test_no, 
                        "Previous Result": "",
                        "Current Result": curr_result,
                        "Diff": "New File / New Test" if curr_result else "New File (Empty Test Result)"
                    })
        elif not abs_curr_path: # File is removed from current (only in previous directory)
            if not all_test_nos: # Removed file with no summary data
                all_comparison_rows.append({
                    "Path": dir_path,
                    "File": filename,
                    config['test_no_header']: "", 
                    "Previous Result": "",
                    "Current Result": "",
                    "Diff": "Removed File (No Summary Data)"
                })
            else: # Removed file with summary data
                for test_no in all_test_nos:
                    prev_result = prev_map.get(test_no, "")
                    all_comparison_rows.append({
                        "Path": dir_path,
                        "File": filename,
                        config['test_no_header']: test_no, 
                        "Previous Result": prev_result,
                        "Current Result": "",
                        "Diff": "Removed File / Removed Test" if prev_result else "Removed File (Empty Test Result)"
                    })
        else: # File exists in both previous and current (standard comparison)
            if not all_test_nos and abs_prev_path and abs_curr_path:
                 # Case where a common file exists but has no summary data in either,
                 # or both have no summary data. This indicates an issue with logs.
                all_comparison_rows.append({
                    "Path": dir_path,
                    "File": filename,
                    config['test_no_header']: "", 
                    "Previous Result": "",
                    "Current Result": "",
                    "Diff": "Common File (No Summary Data in Either)"
                })

            for test_no in all_test_nos:
                prev_result = prev_map.get(test_no, "")
                curr_result = curr_map.get(test_no, "")

                diff_status = ""
                if prev_result == "" and curr_result != "":
                    diff_status = "New Test"
                elif prev_result != "" and curr_result == "":
                    diff_status = "Removed Test"
                elif prev_result != "" and curr_result != "":
                    if prev_result == curr_result:
                        diff_status = "No Change"
                    else:
                        diff_status = f"Changed: {prev_result} -> {curr_result}"
                else:
                    diff_status = "N/A (Both Empty)"

                all_comparison_rows.append({
                    "Path": dir_path,
                    "File": filename,
                    config['test_no_header']: test_no, 
                    "Previous Result": prev_result,
                    "Current Result": curr_result,
                    "Diff": diff_status
                })

    # The column name for Test ID in the final Excel output needs to be dynamic based on config
    df = pd.DataFrame(all_comparison_rows, columns=[
        "Path", "File", config['test_no_header'], "Previous Result", "Current Result", "Diff"
    ])

    try:
        df.to_excel(output_excel_file, index=False)
        _log_message(LOG_LEVEL_INFO, f"\nComparison report generated successfully: '{output_excel_file}'")
    except Exception as e:
        _log_message(LOG_LEVEL_ERROR, f"Error writing Excel file '{output_excel_file}': {e}")

# --- Configuration and Dummy Data Generation ---
if __name__ == "__main__":
    # Define your previous and current test results directories
    PREVIOUS_RESULTS_DIR = "previous_day_results"
    CURRENT_RESULTS_DIR = "current_day_results"
    OUTPUT_EXCEL_FILENAME = "TestSummaryComparisonReport.xlsx"

    # --- SCRIPT CONFIGURATION SECTION ---
    # Customize these values based on your log file format.
    # This dictionary will be passed to parsing functions.
    PARSING_CONFIG = {
        'summary_section_start': "Test Result Summary", 
        'test_no_header': "Test_ID",                                       
        'test_result_header': "Test_Result"                                  
    }
    # ------------------------------------

    # --- MACRO TO ENABLE/DISABLE DUMMY DATA GENERATION ---
    # Set to True to create dummy directories and log files for testing.
    # Set to False if you have your own log files and directories already set up.
    GENERATE_DUMMY_DATA = True 
    # -----------------------------------------------------

    # --- SCRIPT LOG LEVEL CONTROL ---
    # Set the global log level for the script.
    # LOG_LEVEL_NONE    = 0: No log output (except explicit uncaught errors)
    # LOG_LEVEL_ERROR   = 1: Only errors
    # LOG_LEVEL_WARNING = 2: Errors and warnings
    # LOG_LEVEL_INFO    = 3: Errors, warnings, and general progress info
    # LOG_LEVEL_DEBUG   = 4: All available logs, including verbose parsing details
    _SCRIPT_LOG_LEVEL = LOG_LEVEL_INFO 
    # -------------------------------

    if GENERATE_DUMMY_DATA:
        if os.path.exists(PREVIOUS_RESULTS_DIR):
            _log_message(LOG_LEVEL_INFO, f"\nRemoving existing dummy directory: {PREVIOUS_RESULTS_DIR}")
            shutil.rmtree(PREVIOUS_RESULTS_DIR)
        if os.path.exists(CURRENT_RESULTS_DIR):
            _log_message(LOG_LEVEL_INFO, f"Removing existing dummy directory: {CURRENT_RESULTS_DIR}")
            shutil.rmtree(CURRENT_RESULTS_DIR)

        os.makedirs(os.path.join(PREVIOUS_RESULTS_DIR, "module_A", "sub_module_1"), exist_ok=True)
        os.makedirs(os.path.join(PREVIOUS_RESULTS_DIR, "module_B"), exist_ok=True)
        os.makedirs(os.path.join(PREVIOUS_RESULTS_DIR, "module_B", "nested_B"), exist_ok=True)
        os.makedirs(os.path.join(PREVIOUS_RESULTS_DIR, "module_D"), exist_ok=True)

        os.makedirs(os.path.join(CURRENT_RESULTS_DIR, "module_A", "sub_module_1"), exist_ok=True)
        os.makedirs(os.path.join(CURRENT_RESULTS_DIR, "module_B"), exist_ok=True)
        os.makedirs(os.path.join(CURRENT_RESULTS_DIR, "module_B", "nested_B"), exist_ok=True)
        os.makedirs(os.path.join(CURRENT_RESULTS_DIR, "module_C"), exist_ok=True)
        os.makedirs(os.path.join(CURRENT_RESULTS_DIR, "module_A", "new_submodule"), exist_ok=True)


        _log_message(LOG_LEVEL_INFO, "\nCreating dummy log files...")

        # --- Files in both previous and current (common files) ---
        with open(os.path.join(PREVIOUS_RESULTS_DIR, "module_A", "sub_module_1", "test_suite_01.log"), "w") as f:
            f.write("Some header info...\n")
            f.write("Logs during execution...\n")
            f.write("Test Result Summary\n") 
            f.write("Script End Time: 08:00:00 AM\n")
            f.write("Total Run Time: 0:01:00\n")
            f.write("Test_ID Test_Result Description          Error Factor\n") 
            f.write("-----------------------------------------\n")
            f.write("TC_0001 PASS\n") 
            f.write("TID_002 PASS\n") 
            f.write("ABC_003 * FAIL             UNKNOWN_FAILURE\n") 
            f.write("XYZ_004 - SKIP\n") 
            f.write('A1005 PASS\n') 
            f.write("Z9997 PASS\n") 
            f.write("Logs after summary...\n")

        with open(os.path.join(CURRENT_RESULTS_DIR, "module_A", "sub_module_1", "test_suite_01.log"), "w") as f:
            f.write("Some header info...\n")
            f.write("Logs during execution...\n")
            f.write("Test Result Summary\n") 
            f.write("Script End Time: 08:30:00 AM\n")
            f.write("Total Run Time: 0:01:15\n")
            f.write("Test_ID Test_Result Description          Error Factor\n") 
            f.write("-----------------------------------------\n")
            f.write("TC_0001 PASS\n")
            f.write("TID_002 * FAIL             PREVIOUSLY_PASSED\n") 
            f.write("ABC_003 * FAIL             UNKNOWN_FAILURE\n")
            f.write("XYZ_004 PASS\n") 
            f.write("A1005 PASS\n")
            f.write("M5556 PASS\n") 
            f.write("Logs after summary...\n")

        with open(os.path.join(PREVIOUS_RESULTS_DIR, "module_B", "component_test.log"), "w") as f:
            f.write("Component test logs...\n")
            f.write("Test Result Summary\n") 
            f.write("Test_ID Test_Result\n") 
            f.write("----------\n")
            f.write("COMP_10 PASS\n") 
            f.write("COMP_11 PASS\n") 
            f.write("COMP_12 * FAIL\n") 
            f.write("COMP_13 - SKIP\n") 

        with open(os.path.join(CURRENT_RESULTS_DIR, "module_B", "component_test.log"), "w") as f:
            f.write("Component test logs...\n")
            f.write("Test Result Summary\n") 
            f.write("Test_ID Test_Result\n") 
            f.write("----------\n")
            f.write("COMP_10 PASS\n")
            f.write("COMP_11 PASS\n")
            f.write("COMP_12 * FAIL\n")
            f.write("COMP_13 - SKIP\n")

        with open(os.path.join(PREVIOUS_RESULTS_DIR, "module_B", "nested_B", "deep_test.log"), "w") as f:
            f.write("Deep nested test logs...\n")
            f.write("Test Result Summary\n") 
            f.write("Test_ID Test_Result\n") 
            f.write("----------\n")
            f.write("DPTH_1 PASS\n") 
            f.write("DPTH_2 PASS\n") 

        with open(os.path.join(CURRENT_RESULTS_DIR, "module_B", "nested_B", "deep_test.log"), "w") as f:
            f.write("Deep nested test logs...\n")
            f.write("Test Result Summary\n") 
            f.write("Test_ID Test_Result\n") 
            f.write("----------\n")
            f.write("DPTH_1 * FAIL\n") 
            f.write("DPTH_2 PASS\n")
            f.write("DPTH_3 PASS\n") 

        # --- Files only in current_day_results (New Files) ---
        with open(os.path.join(CURRENT_RESULTS_DIR, "module_C", "new_feature_test.log"), "w") as f:
            f.write("New feature logs...\n")
            f.write("Test Result Summary\n") 
            f.write("Test_ID Test_Result\n") 
            f.write("----------\n")
            f.write("FEAT_A01 PASS\n")
            f.write("FEAT_A02 PASS\n")
            f.write("FEAT_A03 - SKIP\n")

        with open(os.path.join(CURRENT_RESULTS_DIR, "module_A", "new_submodule", "another_new_test.log"), "w") as f:
            f.write("This is a new log file with no summary section yet.\n")
            f.write("Only some random log lines.\n")
        
        # --- Files only in previous_day_results (Removed Files) ---
        with open(os.path.join(PREVIOUS_RESULTS_DIR, "module_D", "old_feature_test.log"), "w") as f:
            f.write("Old feature logs...\n")
            f.write("Test Result Summary\n") 
            f.write("Test_ID Test_Result\n") 
            f.write("----------\n")
            f.write("OLD_F1 PASS\n")
            f.write("OLD_F2 * FAIL\n")
            f.write("OLD_F3 PASS\n")

        with open(os.path.join(PREVIOUS_RESULTS_DIR, "module_B", "old_removed_test.log"), "w") as f:
            f.write("This log file was removed.\n")
            f.write("It had no summary section.\n")

        # --- Dummy dotfile to ensure it's ignored ---
        with open(os.path.join(PREVIOUS_RESULTS_DIR, ".DS_Store"), "w") as f:
            f.write("This is a system dotfile.")
        with open(os.path.join(CURRENT_RESULTS_DIR, ".some_config"), "w") as f:
            f.write("This is a config dotfile.")


        _log_message(LOG_LEVEL_INFO, "Dummy log files created. Running comparison...\n")

    # Run the comparison
    compare_test_summaries(PREVIOUS_RESULTS_DIR, CURRENT_RESULTS_DIR, OUTPUT_EXCEL_FILENAME, PARSING_CONFIG)
