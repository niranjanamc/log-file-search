import re
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, colorchooser

# Debug macro
DEBUG = True

def debug_print(message):
    if DEBUG:
        print(message)

class LogFileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Log File Search")
        
        # Set application icon
        self.root.iconbitmap('file_search_icon.ico')  # Ensure 'file_search_icon.ico' is in the same directory

        # Create menu bar
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open", command=self.open_file)

        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Cut", command=lambda: self.root.focus_get().event_generate('<<Cut>>'))
        self.edit_menu.add_command(label="Copy", command=lambda: self.root.focus_get().event_generate('<<Copy>>'))
        self.edit_menu.add_command(label="Paste", command=lambda: self.root.focus_get().event_generate('<<Paste>>'))

        # Report menu
        self.report_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Report", menu=self.report_menu)
        self.report_menu.add_command(label="Add the selected line to report", command=self.add_line_to_report)

        # Pattern menu
        self.pattern_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Pattern", menu=self.pattern_menu)
        self.pattern_menu.add_command(label="Import patterns json", command=self.import_json_filters)
        self.pattern_menu.add_command(label="New Pattern", command=self.add_new_pattern)
        self.pattern_menu.add_command(label="Export Patterns", command=self.export_patterns)
        
        # Adjust layout to prevent overlapping
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        self.left_pane = tk.PanedWindow(self.paned_window, orient=tk.VERTICAL)
        self.paned_window.add(self.left_pane)

        self.top_frame = tk.Frame(self.left_pane)
        self.bottom_frame = tk.Frame(self.left_pane)
        
        self.left_pane.add(self.top_frame)
        self.left_pane.add(self.bottom_frame)
        
        self.file_text = tk.Text(self.top_frame, wrap='word', height=20, width=80)
        self.file_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.file_text.config(state=tk.DISABLED)  # Disable editing
        
        self.scrollbar = tk.Scrollbar(self.top_frame, command=self.file_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_text.config(yscrollcommand=self.scrollbar.set)
        
        # Create a frame for the search bar and search button
        self.search_frame = tk.Frame(self.bottom_frame)
        self.search_frame.pack(fill=tk.X)

        # Search entry
        self.pattern_entry = tk.Entry(self.search_frame)
        self.pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=1)

        # Start search when Enter key is pressed
        self.pattern_entry.bind("<Return>", lambda event: self.update_search_patterns())

        # Search button moved to the right of the search entry
        self.search_button = tk.Button(self.search_frame, text="Search", command=self.update_search_patterns)
        self.search_button.pack(side=tk.LEFT)

        # Add case sensitivity toggle button
        self.case_sensitive = tk.BooleanVar(value=False)
        self.case_sensitive_button = tk.Checkbutton(self.search_frame, text="Aa", variable=self.case_sensitive, command=self.update_search_patterns)
        self.case_sensitive_button.pack(side=tk.LEFT)

        self.result_text = tk.Text(self.bottom_frame, wrap='word')
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.result_scrollbar = tk.Scrollbar(self.bottom_frame, command=self.result_text.yview)
        self.result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=self.result_scrollbar.set)
        # Bind click event to result_text
        self.result_text.bind("<Button-1>", self.on_result_click)
        
        self.file_path = None
        self.report_file_path = None  # Initialize report file path

        # Create a status bar at the bottom to display the file path
        self.status_bar = tk.Label(root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Frame for pattern buttons with scrollbar
        self.pattern_buttons_frame = tk.Frame(self.paned_window, width=100)
        self.pattern_buttons_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.pattern_buttons_frame)

        self.pattern_buttons_canvas = tk.Canvas(self.pattern_buttons_frame)
        self.pattern_buttons_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.pattern_buttons_scrollbar = tk.Scrollbar(self.pattern_buttons_frame, orient=tk.VERTICAL, command=self.pattern_buttons_canvas.yview)
        self.pattern_buttons_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.pattern_buttons_canvas.configure(yscrollcommand=self.pattern_buttons_scrollbar.set)
        self.pattern_buttons_canvas.bind('<Configure>', lambda e: self.pattern_buttons_canvas.configure(scrollregion=self.pattern_buttons_canvas.bbox("all")))

        self.pattern_buttons_inner_frame = tk.Frame(self.pattern_buttons_canvas)
        self.pattern_buttons_canvas.create_window((0, 0), window=self.pattern_buttons_inner_frame, anchor="nw")

        self.patterns = {}  # Initialize patterns dictionary
        self.pattern_buttons = {}  # Dictionary to store pattern buttons
        self.search_patterns_list = []  # Initialize search patterns list
        self.imported_patterns = {}  # Store imported patterns

        # Add a vertical separator between the left and right panes
        self.paned_window.add(self.pattern_buttons_frame, stretch="always")

        # Add a horizontal separator between the top and bottom frames
        self.left_pane.add(self.top_frame, stretch="always")
        self.left_pane.add(self.bottom_frame, stretch="always")

    def open_file(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        if self.file_path:
            debug_print(f"File selected: {self.file_path}")
            self.display_file_content()
        else:
            # Show error if no file was selected
            messagebox.showwarning("No File Selected", "Please select a log file.")
    
    def display_file_content(self):
        try:
            with open(self.file_path, 'r') as file:
                lines = file.readlines()

            # Enable the text widget to insert content
            self.file_text.config(state=tk.NORMAL)
            self.file_text.delete(1.0, tk.END)
            for idx, line in enumerate(lines, start=1):
                self.file_text.insert(tk.END, f"{idx}: {line}")
            # Disable editing again
            self.file_text.config(state=tk.DISABLED)

            # Update status bar with the file path
            self.status_bar.config(text=self.file_path)
            debug_print(f"File content displayed for: {self.file_path}")
        except Exception as e:
            messagebox.showerror(
                "Error Opening File", f"An error occurred while opening the file:\n{e}"
            )
            debug_print(f"Error opening file: {e}")

    def update_search_patterns(self):
        patterns = self.pattern_entry.get().split('|')
        self.search_patterns_list = []

        # Add patterns from the entry with respective colors from JSON or default color black
        for pattern in patterns:
            if pattern:
                color = self.imported_patterns.get(pattern, {}).get('highlight_color', 'black')
                self.search_patterns_list.append((pattern, color))

        debug_print(f"Search patterns: {self.search_patterns_list}")
        self.perform_search()

    def perform_search(self):
        compiled_patterns = [
            (re.compile(pattern) if self.case_sensitive.get() else re.compile(pattern, re.IGNORECASE), color)
            for pattern, color in self.search_patterns_list
        ]
        
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        
        self.clear_highlights()
        
        for idx, line in enumerate(lines, start=1):
            for pattern, color in compiled_patterns:
                if pattern.search(line):
                    tag_name = f"highlight_{pattern.pattern}_{idx}"
                    self.result_text.insert(tk.END, f"{idx}: {line}", (tag_name,))
                    self.result_text.tag_config(tag_name, foreground=color)
                    self.file_text.tag_add(tag_name, f"{idx}.0", f"{idx}.0 lineend")
                    self.file_text.tag_config(tag_name, foreground=color)
        
        self.file_text.config(state=tk.DISABLED)
        debug_print("Search completed and results updated.")

    def add_line_to_report(self):
        try:
            # Get the selected text from result_text
            selected_text = self.result_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            # Show warning if no text is selected
            messagebox.showwarning("No Selection", "Please select a line to add to the report.")
            return

        # Ask where to save the report if not already specified
        if not self.report_file_path:
            self.report_file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Report As"
            )
            if not self.report_file_path:
                # User canceled the dialog
                return

        try:
            with open(self.report_file_path, 'a') as report_file:
                report_file.write(selected_text + '\n')
            debug_print(f"Added line to report: {selected_text}")
        except Exception as e:
            messagebox.showerror(
                "Write Error", f"Failed to write to report file:\n{e}"
            )
            debug_print(f"Error writing to report file: {e}")

    def on_result_click(self, event):
        # Remove any existing highlight in result_text
        self.result_text.tag_remove("highlight_result", "1.0", "end")

        # Get the index of the clicked line in result_text
        index = self.result_text.index("@%s,%s linestart" % (event.x, event.y))
        # Highlight the selected line in result_text
        self.result_text.tag_add("highlight_result", index, "%s lineend" % index)
        self.result_text.tag_config("highlight_result", background="lightblue")

        # Get the full text of the clicked line
        line_content = self.result_text.get(index, "%s lineend" % index)

        # Extract line number from the line content
        match = re.match(r"(\d+):", line_content)
        if match and self.file_path:
            line_number = int(match.group(1))

            # Scroll file_text to the corresponding line
            self.file_text.see(f"{line_number}.0")

            # Enable the text widget to update tags
            self.file_text.config(state=tk.NORMAL)
            # Remove previous highlights
            self.file_text.tag_remove("highlight_file", "1.0", "end")
            # Highlight the line in file_text
            self.file_text.tag_add("highlight_file", f"{line_number}.0", f"{line_number}.0 lineend")
            self.file_text.tag_config("highlight_file", background="yellow")
            # Disable editing again
            self.file_text.config(state=tk.DISABLED)
            debug_print(f"Highlighted line {line_number} in main window.")
        else:
            # Do nothing if line number cannot be determined or file is not opened
            pass

    def import_json_filters(self):
        json_file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not json_file_path:
            return

        try:
            with open(json_file_path, 'r') as json_file:
                self.patterns = json.load(json_file)
                self.imported_patterns = {v['pattern']: v for v in self.patterns.values()}  # Store imported patterns
            self.create_pattern_buttons()
            self.update_main_window_with_patterns()
            self.pattern_entry.delete(0, tk.END)  # Clear the search bar pattern
            debug_print(f"Imported JSON filters from: {json_file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON file:\n{e}")
            debug_print(f"Error loading JSON file: {e}")

    def create_pattern_buttons(self):
        for widget in self.pattern_buttons_inner_frame.winfo_children():
            widget.destroy()

        for pattern_name, pattern_info in self.patterns.items():
            button = tk.Button(
                self.pattern_buttons_inner_frame, 
                text=pattern_info['pattern'], 
                command=lambda p=pattern_info: self.toggle_pattern(p)
            )
            button.pack(fill=tk.X)
            self.pattern_buttons[pattern_info['pattern']] = button
        debug_print("Pattern buttons created.")
        #self.pattern_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)

    def toggle_pattern(self, pattern_info):
        pattern = pattern_info['pattern']
        color = pattern_info['highlight_color']
        current_patterns = self.pattern_entry.get().split('|')
        
        if (pattern in current_patterns):
            current_patterns.remove(pattern)
            self.pattern_buttons[pattern].config(bg='SystemButtonFace', fg='black')
        else:
            current_patterns.append(pattern)
            self.pattern_buttons[pattern].config(bg='SystemButtonFace', fg=color)
        
        new_patterns = '|'.join(filter(None, current_patterns))  # Remove empty strings
        self.pattern_entry.delete(0, tk.END)
        self.pattern_entry.insert(0, new_patterns)
        self.update_search_patterns()
        debug_print(f"Toggled pattern: {pattern}, current patterns: {current_patterns}")

    def update_main_window_with_patterns(self):
        compiled_patterns = [
            (re.compile(pattern_info['pattern']), pattern_info['highlight_color'])
            for pattern_info in self.patterns.values()
        ]
        
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        
        self.file_text.config(state=tk.NORMAL)
        for idx, line in enumerate(lines, start=1):
            for pattern, color in compiled_patterns:
                if pattern.search(line):
                    self.file_text.tag_add(f"highlight_{pattern.pattern}", f"{idx}.0", f"{idx}.0 lineend")
                    self.file_text.tag_config(f"highlight_{pattern.pattern}", foreground=color)
        self.file_text.config(state=tk.DISABLED)
        debug_print("Main window updated with patterns.")

    def clear_highlights(self):
        self.file_text.config(state=tk.NORMAL)
        self.file_text.tag_remove("highlight_file", "1.0", "end")
        self.result_text.delete(1.0, tk.END)  # Clear the search results window
        self.file_text.config(state=tk.DISABLED)
        debug_print("Cleared all highlights.")

    def add_new_pattern(self):
        pattern = simpledialog.askstring("New Pattern", "Enter the pattern:")
        if not pattern:
            return
        color = colorchooser.askcolor(title="Choose highlight color")[1]
        if not color:
            return

        self.imported_patterns[pattern] = {'pattern': pattern, 'highlight_color': color}
        self.create_pattern_buttons()
        self.add_pattern_button(pattern, color)
        debug_print(f"Added new pattern: {pattern} with color: {color}")

    def add_pattern_button(self, pattern, color):
        button = tk.Button(
            self.pattern_buttons_inner_frame, 
            text=pattern, 
            command=lambda p=pattern: self.toggle_pattern({'pattern': p, 'highlight_color': color})
        )
        button.pack(fill=tk.X)
        self.pattern_buttons[pattern] = button
        debug_print(f"Added button for pattern: {pattern}")
        # self.pattern_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)

    def export_patterns(self):
        export_file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Patterns As"
        )
        if not export_file_path:
            return

        try:
            with open(export_file_path, 'w') as export_file:
                json.dump(self.imported_patterns, export_file, indent=4)
            debug_print(f"Exported patterns to: {export_file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export patterns:\n{e}")
            debug_print(f"Error exporting patterns: {e}")

# Remove the on_file_drop method since drag and drop is disabled
# def on_file_drop(self, event):
#     # ...existing code...

# Use tk.Tk() instead of TkinterDnD.Tk()
if __name__ == "__main__":
    root = tk.Tk()
    app = LogFileSearchApp(root)
    root.mainloop()