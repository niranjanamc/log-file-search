import re
import tkinter as tk
from tkinter import filedialog, messagebox
# Remove the import of tkinterdnd2
# from tkinterdnd2 import TkinterDnD, Tk

class LogFileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Log File Search")
        
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
        
        self.paned_window = tk.PanedWindow(root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)
        
        self.top_frame = tk.Frame(self.paned_window)
        self.bottom_frame = tk.Frame(self.paned_window)
        
        self.paned_window.add(self.top_frame)
        self.paned_window.add(self.bottom_frame)
        
        self.file_text = tk.Text(self.top_frame, wrap='word', height=20, width=80)
        self.file_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.file_text.config(state=tk.DISABLED)  # Disable editing
        
        self.scrollbar = tk.Scrollbar(self.top_frame, command=self.file_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_text.config(yscrollcommand=self.scrollbar.set)
        
        # Remove the pattern label
        # self.pattern_label = tk.Label(self.bottom_frame, text="Enter patterns (separated by '|'):")
        # self.pattern_label.pack()

        # Create a frame for the search bar and search button
        self.search_frame = tk.Frame(self.bottom_frame)
        self.search_frame.pack(fill=tk.X)

        # Search entry
        self.pattern_entry = tk.Entry(self.search_frame)
        self.pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=1)

        # Start search when Enter key is pressed
        self.pattern_entry.bind("<Return>", lambda event: self.search_patterns())

        # Search button moved to the right of the search entry
        self.search_button = tk.Button(self.search_frame, text="Search", command=self.search_patterns)
        self.search_button.pack(side=tk.LEFT)

        # Add case sensitivity toggle button
        self.case_sensitive = tk.BooleanVar(value=False)
        self.case_sensitive_button = tk.Checkbutton(self.search_frame, text="Aa", variable=self.case_sensitive)
        self.case_sensitive_button.pack(side=tk.LEFT)

        self.result_text = tk.Text(self.bottom_frame, wrap='word')
        self.result_text.pack(fill=tk.BOTH, expand=1)
        # Bind click event to result_text
        self.result_text.bind("<Button-1>", self.on_result_click)
        
        self.file_path = None
        # Remove Open Log File button
        # self.open_file_button = tk.Button(root, text="Open Log File", command=self.open_file)
        # self.open_file_button.pack()
        
        self.report_file_path = None  # Initialize report file path

        # Create a status bar at the bottom to display the file path
        self.status_bar = tk.Label(root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Remove drag and drop initialization
        # root.drop_target_register('*')
        # root.dnd_bind('<<Drop>>', self.on_file_drop)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        if self.file_path:
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
        except Exception as e:
            messagebox.showerror(
                "Error Opening File", f"An error occurred while opening the file:\n{e}"
            )
    
    def search_patterns(self):
        if not self.file_path:
            messagebox.showwarning("No File", "Please select a log file first.")
            return
        
        patterns = self.pattern_entry.get()
        if not patterns:
            messagebox.showwarning("No Patterns", "Please enter search patterns.")
            return
        
        pattern_list = patterns.split('|')
        compiled_patterns = [
            re.compile(pattern) if self.case_sensitive.get() else re.compile(pattern, re.IGNORECASE)
            for pattern in pattern_list
        ]
        
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        
        self.result_text.delete(1.0, tk.END)
        for idx, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in compiled_patterns):
                self.result_text.insert(tk.END, f"{idx}: {line}")
    
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
        except Exception as e:
            messagebox.showerror(
                "Write Error", f"Failed to write to report file:\n{e}"
            )

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
        else:
            # Do nothing if line number cannot be determined or file is not opened
            pass

    # Remove the on_file_drop method since drag and drop is disabled
    # def on_file_drop(self, event):
    #     # ...existing code...

# Use tk.Tk() instead of TkinterDnD.Tk()
if __name__ == "__main__":
    root = tk.Tk()
    app = LogFileSearchApp(root)
    root.mainloop()