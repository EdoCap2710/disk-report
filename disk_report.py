import os
import shutil
import tkinter as tk
from tkinter import filedialog, ttk

app_state = {
    "path": "/",
    "sort_descending": False,
}

item_sizes = {}

palette = {
    "background": "#111827",
    "surface": "#1e293b",
    "text": "#e2e8f0",
    "accent": "#2dd4bf",
    "hover": "#334155",
}

# Creates the GUI window
window = tk.Tk()
window.title("Disk Report")
window.geometry("900x600")
window.minsize(600, 400)
window.configure(background=palette["background"])

# Assigns the program icon
file_path = os.path.dirname(__file__)
icon_path = os.path.join(file_path, "assets", "disk_report.png")
app_icon = tk.PhotoImage(file=icon_path)
window.iconphoto(True, app_icon)

# Configures the application theme and widget styles
style = ttk.Style(window)
style.theme_use("clam")
style.configure(
    "TFrame",
    background=palette["background"],
)
style.configure(
    "TLabel",
    background=palette["background"],
    foreground=palette["text"],
)
style.configure(
    "Treeview",
    background=palette["surface"],
    fieldbackground=palette["surface"],
    foreground=palette["text"],
)
style.configure(
    "Treeview.Heading",
    background=palette["surface"],
    foreground=palette["text"],
)
style.configure(
    "TButton",
    background=palette["surface"],
    foreground=palette["text"],
)
style.configure(
    "Horizontal.TProgressbar",
    background=palette["accent"],
    troughcolor=palette["surface"],
)
style.configure(
    "Vertical.TScrollbar",
    background=palette["surface"],
    troughcolor=palette["background"],
    arrowcolor=palette["text"],
)
style.map(
    "Vertical.TScrollbar",
    background=[
        ("disabled", palette["surface"]),
        ("pressed", palette["accent"]),
        ("active", palette["hover"]),
    ],
)

# Creates the frame containing the function buttons
toolbar = ttk.Frame(window)
toolbar.pack(fill="x", padx=5, pady=5)

# Creates the GUI label
status_label = ttk.Label(window, text="Press to scan")
status_label.pack(pady=5)

# Creates the GUI bar
usage_bar = ttk.Progressbar(
    window,
    orient="horizontal",
    mode="determinate",
    maximum=100,
    value=50,
    length=280,
)
usage_bar.pack(fill="x", padx=10, pady=5)

# Creates the frame containing the GUI treeview
tree_frame = ttk.Frame(window)
tree_frame.pack(expand=True, fill="both", padx=10, pady=10)

# Creates the GUI treeview
file_tree = ttk.Treeview(tree_frame)
file_tree.pack(expand=True, fill="both", side="left")
tree_identifier = file_tree.insert("", "end", text="")
file_tree.configure(columns=("size",))
file_tree.heading("#0", text="Path")
file_tree.column("#0", width=600, minwidth=200, stretch=True)
file_tree.heading("size", text="Size")
file_tree.column(
    "size",
    anchor="e",
    width=140,
    minwidth=100,
    stretch=False,
)

# Creates a scrollbar for the filetree
tree_scrollbar = ttk.Scrollbar(
    tree_frame,
    orient="vertical",
    command=file_tree.yview,
)
tree_scrollbar.pack(side="right", fill="y")
file_tree.configure(yscrollcommand=tree_scrollbar.set)


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
        "percentage_used": percentage_used,
    }
    return report


# Formats a size in bytes as a human-readable string (B, KiB, MiB...)
def format_size(size_bytes):
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = size_bytes
    for unit in units:
        if value < 1024 and unit == "B":
            return f"{value} {unit}"
        elif value < 1024:
            return f"{value:.2f} {unit}"
        value = value / 1024
    return f"{value:.2f} PiB"


# Populates the tree recursively and returns its total size in bytes
def scan_directory(path, parent_id, level=0):
    dir_size = 0
    with os.scandir(path) as scan:
        for element in scan:
            if element.is_symlink():
                file_tree.insert(
                    parent_id,
                    "end",
                    text=f"{element.name}",
                    values=("Symlink",),
                )
            elif element.is_file():
                file_size = element.stat().st_size
                dir_size = dir_size + file_size
                file_identifier = file_tree.insert(
                    parent_id,
                    "end",
                    text=f"{element.name}",
                    values=(format_size(file_size),),
                )
                item_sizes[file_identifier] = file_size
            elif element.is_dir():
                dir_identifier = file_tree.insert(
                    parent_id,
                    "end",
                    text=f"{element.name}",
                )
                try:
                    dir_size = dir_size + scan_directory(
                        element.path,
                        dir_identifier,
                        level + 1,
                    )
                except PermissionError:
                    file_tree.set(
                        dir_identifier,
                        "size",
                        "Permission Err.",
                    )
                except OSError:
                    file_tree.set(
                        dir_identifier,
                        "size",
                        "Error",
                    )

    file_tree.set(parent_id, "size", format_size(dir_size))
    item_sizes[parent_id] = dir_size
    return dir_size


# Updates the filesystem usage label and progress bar
def update_report():
    try:
        report = disk_usage_report(app_state['path'])
        updated_report = (
            f"Analyzed disk is {report['analyzed_disk']}\n"
            f"Total Space: {report['total_gib']:.2f} GiB\n"
            f"Used Space: {report['used_gib']:.2f} GiB\n"
            f"Free Space: {report['free_gib']:.2f} GiB\n"
            f"Used Percentage: {report['percentage_used']:.1f} %"
        )
        usage_bar.configure(value=report['percentage_used'])
    except FileNotFoundError:
        updated_report = "Directory not found"
        usage_bar.configure(value=0)
    except PermissionError:
        updated_report = (
            "The program lacks the necessary permission for this directory"
        )
        usage_bar.configure(value=0)
    status_label.configure(text=updated_report)


# Lets the user choose a different directory
def choose_disk():
    selected_path = filedialog.askdirectory(
        parent=window,
        title="Choose Disk",
        mustexist=True,
    )
    if selected_path:
        app_state['path'] = selected_path
        update_report()
        file_tree.item(tree_identifier, text=f"{selected_path}")
        for children in file_tree.get_children(tree_identifier):
            file_tree.delete(children)
        item_sizes.clear()
        try:
            scan_directory(app_state['path'], tree_identifier)
        except PermissionError:
            file_tree.set(
                tree_identifier,
                "size",
                "Permission Err.",
            )
        except OSError:
            file_tree.set(
                tree_identifier,
                "size",
                "Error",
            )


# Sorts the file tree in ascending or descending size
def sort_tree(parent_id):
    children = file_tree.get_children(parent_id)
    sorted_children = sorted(
        children,
        key=lambda child: item_sizes.get(child, -1),
        reverse=app_state["sort_descending"],
    )
    for position, child in enumerate(sorted_children):
        file_tree.move(child, parent_id, position)
        sort_tree(child)


# Calls the sort_tree function every time the "size" column header is clicked
def on_size_heading_click():
    app_state["sort_descending"] = not app_state["sort_descending"]
    sort_tree(tree_identifier)


window.after(0, choose_disk)  # Makes choose_disk() start at launch

# Creates the button that refreshes filesystem usage statistics
update_button = ttk.Button(
    toolbar,
    text="Update",
    command=update_report,
)
update_button.pack(side="left", padx=5, expand=True, fill=tk.X)
update_report()

# Creates the button to choose the directory
disk_button = ttk.Button(toolbar, text="Choose Disk", command=choose_disk)
disk_button.pack(side="left", padx=5, expand=True, fill=tk.X)

# Makes the size column react to the user click
file_tree.heading("size", command=on_size_heading_click)

window.mainloop()
