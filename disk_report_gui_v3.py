import os
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

app_state = {
    "path": "/"
}

# Creates the GUI window
window = tk.Tk()
window.title("Disk Report")
window.geometry("900x600")
window.minsize(600,400)

# Creates the frame containig the functions buttons
toolbar = ttk.Frame(window)
toolbar.pack(fill = "x", padx = 5, pady = 5)

# Creates the GUI label
status_label = ttk.Label(window, text="Press to scan")
status_label.pack(pady = 5)

# Creates the GUI bar
usage_bar = ttk.Progressbar(window, orient = "horizontal", mode = "determinate", maximum = 100, value = 50, length = 280)
usage_bar.pack(fill = "x", padx = 10, pady = 5)

# Creates the frame containing the GUI treeview
tree_frame = ttk.Frame(window)
tree_frame.pack(expand = True, fill = "both", padx = 10, pady = 10)

# Creates the GUI treeview
file_tree = ttk.Treeview(tree_frame)
file_tree.pack(expand = True, fill = "both", side = "left")
tree_identifier = file_tree.insert("", "end", text = "")
file_tree.configure(columns = ("size",))
file_tree.heading("#0", text = "Path")
file_tree.column("#0", width = 600, minwidth = 200, stretch = True)
file_tree.heading("size", text = "Size(MiB)")
file_tree.column("size", anchor = "e", width = 140, minwidth = 100, stretch = False)

# Creates a scrollbar for the filetree
tree_scrollbar = ttk.Scrollbar(tree_frame, orient = "vertical", command = file_tree.yview)
tree_scrollbar.pack(side = "right", fill = "y")
file_tree.configure(yscrollcommand = tree_scrollbar.set)

# Checks the chosen disk's filesystem and returns its usage information
def disk_usage_report(path):
    usage = shutil.disk_usage(path)
    total = usage.total
    used = usage.used
    free = usage.free

    total_gib = total / (1024 ** 3)
    used_gib = used / (1024 ** 3)
    free_gib = free / (1024 ** 3)

    percentage_used = used / total * 100

    report = {
        "total_gib": total_gib,
        "used_gib": used_gib,
        "free_gib": free_gib,
        "analyzed_disk": path,
        "percentage_used": percentage_used
    }
    return report

# Populates the GUI tree and scans a directory for files and sub-directories recursively
# then returns the directory's total file size in bytes
def scan_directory(path, parent_id, level = 0):
    dir_size = 0
    with os.scandir(path) as scan:
        for element in scan:
            if element.is_file():
                file_size_Mib = element.stat().st_size / (1024 ** 2)
                dir_size = dir_size + element.stat().st_size
                file_tree.insert(parent_id, "end", text = f"{element.name}", values=(f"{file_size_Mib:.2f}", ))
            elif element.is_dir():
                dir_identifier = file_tree.insert(parent_id, "end", text = f"{element.name}")
                dir_size = dir_size + scan_directory(element.path, dir_identifier, level + 1)
    file_tree.set(parent_id, "size", f"{(dir_size / (1024 ** 2)):.2f}")
    return dir_size

# Updates the filesystem usage label and progress bar.
def update_report():
    try:
        report = disk_usage_report(app_state['path'])
        updated_report = f"Analyzed disk is {report['analyzed_disk']}\nTotal Space: {report['total_gib']:.2f} GiB\nUsed Space: {report['used_gib']:.2f} GiB\nFree Space: {report['free_gib']:.2f} GiB\nUsed Percentage: {report['percentage_used']:.1f} %"
        usage_bar.configure(value = report['percentage_used'])
    except FileNotFoundError:
        updated_report = ("Directory not found")
        usage_bar.configure(value = 0)
    except PermissionError:
        updated_report = ("The program lacks the necessary permission for this directory")
        usage_bar.configure(value = 0)
    status_label.configure(text = updated_report)

# Lets the user choose a different directory
def choose_disk():
    selected_path = filedialog.askdirectory(parent = window, title = "Choose Disk", mustexist = True)
    if selected_path:
        app_state['path'] = selected_path
        update_report()
        file_tree.item(tree_identifier, text=f"{selected_path}")
        for children in file_tree.get_children(tree_identifier):
            file_tree.delete(children)
        scan_directory(app_state['path'], tree_identifier)

window.after(0, choose_disk)  # Makes choose_disk() start at launch


# Creates the button that refreshes filesystem usage statistics.
update_button = ttk.Button(toolbar, text="Update", command=update_report)
update_button.pack(side = "left", padx = 5, expand = True, fill = tk.X)
update_report()

# Creates the button to choose the directory
disk_button = ttk.Button(toolbar, text="Choose Disk", command=choose_disk)
disk_button.pack(side = "left", padx = 5, expand = True, fill = tk.X)

window.mainloop()
