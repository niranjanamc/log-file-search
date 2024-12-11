# log-file-search

## Description
Log File Search is a Python application that allows users to search for patterns in log files using a graphical user interface (GUI). The application supports case-sensitive and case-insensitive searches and allows users to add selected lines to a report. Additionally, users can import JSON files containing predefined search patterns with specific highlight colors.

## Features
- **Open Log Files**: Open and display log files.
- **Search Patterns**: Search for multiple patterns in the log file.
- **Case Sensitivity**: Toggle case-sensitive searches.
- **Highlight Patterns**: Highlight search patterns with specific colors.
- **Add to Report**: Add selected lines to a report file.
- **Import JSON Filters**: Import predefined search patterns from a JSON file.

## Usage
1. **Open Log File**: Use the "File" menu to open a log file.
2. **Search Patterns**: Enter search patterns in the search bar. Patterns should be separated by the '|' character for multiple patterns.
3. **Case Sensitivity**: Toggle the "Aa" button to enable or disable case-sensitive searches.
4. **View Results**: The results of the search will be displayed in the bottom text area with the specified highlight colors.
5. **Add to Report**: Select a line from the results and use the "Report" menu to add the selected line to a report file.
6. **Import JSON Filters**: Use the "Import" menu to import JSON files containing predefined search patterns and their highlight colors.

## Requirements
- Python 3.x
- Tkinter (usually included with Python)

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/log-file-search.git
    ```
2. Navigate to the project directory:
    ```sh
    cd log-file-search
    ```
3. Run the application:
    ```sh
    python3 log_search.py
    ```

## JSON Filters
The JSON file should contain predefined search patterns and their highlight colors. Below is an example of the JSON format:
```json
{
    "Error Pattern": {
        "pattern": "Error",
        "highlight_color": "red"
    },
    "Warning Pattern": {
        "pattern": "Warning",
        "highlight_color": "yellow"
    },
    "Info Pattern": {
        "pattern": "Info",
        "highlight_color": "green"
    }
}