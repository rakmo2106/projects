import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import threading
import json
import os

timer_running = False
is_compact = False

tasks = []

SAVE_FILE = "tasks.json"

def save_tasks():
    with open(SAVE_FILE, "w") as f:
        json.dump(tasks, f)

def load_tasks():
    global tasks
    try:
        with open("tasks.json", "r") as f:
            tasks = json.load(f)
    except FileNotFoundError:
        tasks = []

def add_task():
    base_name = simpledialog.askstring("New Task", "Enter task name:")
    if base_name:
        existing_names = [task["name"] for task in tasks]
        name = base_name
        counter = 1
        while name in existing_names:
            name = f"{base_name}{counter}"
            counter += 1
        tasks.append({"name": name, "duration": 0})
        update_list()
        save_tasks()

def start_timer():
    selected = task_listbox.curselection()
    if not selected:
        messagebox.showinfo("No Task", "Please select a task to start timer.")
        return

    index = selected[0]
    task = tasks[index]

    # Ask user for duration in minutes
    duration = simpledialog.askinteger("Timer Duration", "Enter timer duration in minutes:", minvalue=1, maxvalue=240)
    if duration is None:
        return  # User cancelled input

    total_seconds = duration * 60
    start_time = time.time()

    threading.Thread(target=lambda: run_timer(task, duration)).start()

def start_additional_timer(task, total_seconds):
    # Compact mode again
    root.geometry("250x160")
    task_frame.pack_forget()
    exit_button.pack(pady=5)
    finish_button.pack(pady=5)
    timer_label.config(font=("Arial", 24))

    threading.Thread(target=lambda: run_extra(task, total_seconds)).start()

def run_timer(task, duration):
    total_seconds = duration * 60
    start_time = time.time()

    # Compact mode UI change
    root.geometry("250x160")
    task_frame.pack_forget()
    exit_button.pack(pady=5)
    timer_label.config(font=("Arial", 24))
    finish_button.pack(pady=5)

    messagebox.showinfo("Timer Started", f"Timing: {task['name']} for {duration} minutes")

    global timer_running
    timer_running = True

    remaining = total_seconds
    while remaining > 0 and timer_running:
        hrs = remaining // 3600
        mins = (remaining % 3600) // 60
        secs = remaining % 60
        timer_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
        time.sleep(1)
        remaining -= 1

    # When timer ends or is manually stopped
    end_time = time.time()
    elapsed = round(end_time - start_time, 2)
    task['duration'] += elapsed
    save_tasks()
    update_list()

    # Reset UI to full mode
    root.geometry("")  # Auto-resize
    task_frame.pack()
    exit_button.pack_forget()
    finish_button.pack_forget()
    timer_label.config(font=("Arial", 14))
    timer_label.config(text="00:00")

    # Pop-up with add time options
    if timer_running:  # Timer completed naturally
        root.after(0, lambda: show_timer_done_popup(task, 0))
    else:  # Finished early
        messagebox.showinfo("Finished Early", f"Completed '{task['name']}' early!\nActual time: {format_time(elapsed)}")

    timer_running = False
    
def show_timer_done_popup(task, extra_minutes):
    response = messagebox.askyesno(
        "Timer Done",
        f"Completed '{task['name']}'!\nDo you want to add more time?"
    )
    if response:
        extra = simpledialog.askinteger("Add Time", "Add how many more minutes?", minvalue=1, maxvalue=60)
        if extra:
            start_additional_timer(task, extra * 60)
    else:
        messagebox.showinfo("Nice!", "Great job finishing the task!")

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

def update_list():
    task_listbox.delete(0, tk.END)
    for task in tasks:
        display_name = task['name']
        if task.get("done"):
            display_name = f"✔️ {display_name}"  # Optional symbol
        time_str = format_time(task['duration'])
        task_listbox.insert(tk.END, f"{display_name} - {time_str}")

def toggle_done(event):
    selected = task_listbox.curselection()
    if not selected:
        return
    index = selected[0]
    task = tasks[index]
    task["done"] = not task.get("done", False)
    update_list()
    save_tasks()

def toggle_compact_mode():
    global is_compact
    if is_compact:
        task_frame.pack()
        exit_button.pack_forget()
        finish_button.pack_forget()
        timer_label.config(font=("Arial", 14))
        root.geometry("")
        is_compact = False
    else:
        task_frame.pack_forget()
        exit_button.pack(pady=5)
        finish_button.pack(pady=5)
        timer_label.config(font=("Arial", 24))
        root.geometry("250x160")
        is_compact = True

def stop_timer_early():
    global timer_running
    timer_running = False  # This will break the loop inside run_timer()
    save_tasks()

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode

    bg_color = "#2e2e2e" if dark_mode else "white"
    fg_color = "white" if dark_mode else "black"
    btn_bg = "#444444" if dark_mode else "SystemButtonFace"

    root.configure(bg=bg_color)
    task_frame.configure(bg=bg_color)
    frame.configure(bg=bg_color)

    for widget in task_frame.winfo_children():
        if isinstance(widget, (tk.Button, tk.Listbox)):
            widget.configure(bg=btn_bg, fg=fg_color)
    task_listbox.configure(selectbackground="#555555" if dark_mode else "#cce5ff")

    timer_label.configure(bg=bg_color, fg=fg_color)
    exit_button.configure(bg=btn_bg, fg=fg_color)
    finish_button.configure(bg=btn_bg, fg=fg_color)
    dark_mode_btn.configure(bg=btn_bg, fg=fg_color)

def reset_tasks():
    if messagebox.askyesno("Reset Tasks", "Are you sure you want to delete all tasks?"):
        global tasks
        tasks = []
        update_list()
        save_tasks()  # This is what was missing — update the JSON too

def context_action(action):
    selected = task_listbox.curselection()
    if not selected:
        return
    index = selected[0]
    task = tasks[index]

    if action == "toggle":
        task["done"] = not task.get("done", False)
    elif action == "rename":
        new_name = simpledialog.askstring("Rename Task", "Enter new task name:", initialvalue=task["name"])
        if new_name:
            task["name"] = new_name
    elif action == "delete":
        if messagebox.askyesno("Delete Task", f"Delete '{task['name']}'?"):
            tasks.pop(index)

    update_list()

def show_context_menu(event):
    try:
        task_listbox.selection_clear(0, tk.END)
        task_listbox.selection_set(task_listbox.nearest(event.y))
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()

def delete_task():
    selected = task_listbox.curselection()
    if not selected:
        return
    index = selected[0]
    del tasks[index]
    update_list()
    save_tasks()

def run_extra(task, total_seconds):
    global timer_running
    timer_running = True

    start_time = time.time()
    remaining = total_seconds

    while remaining > 0 and timer_running:
        hrs = remaining // 3600
        mins = (remaining % 3600) // 60
        secs = remaining % 60
        timer_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
        time.sleep(1)
        remaining -= 1

    end_time = time.time()
    elapsed = round(end_time - start_time)

    # ✅ Always count elapsed time
    task['duration'] += elapsed
    save_tasks()
    update_list()

    if timer_running:
        timer_label.config(text="00:00")
        show_timer_done_popup(task, 0)
        root.geometry("")  # Auto-resize
        task_frame.pack()
        exit_button.pack_forget()
        finish_button.pack_forget()
        timer_label.config(font=("Arial", 14))
        timer_label.config(text="00:00")
    else:
        messagebox.showinfo("Stopped", "Timer was stopped early.")
        # ✅ Reset UI even if stopped
        root.geometry("")  # Auto-resize
        task_frame.pack()
        exit_button.pack_forget()
        finish_button.pack_forget()
        timer_label.config(font=("Arial", 14))
        timer_label.config(text="00:00")

    timer_running = False

def delete_word(event):
    entry = event.widget
    index = entry.index(tk.INSERT)
    text = entry.get()

    if index == 0:
        return "break"

    # Find previous space
    i = index - 1
    while i > 0 and text[i] != ' ':
        i -= 1

    entry.delete(i, index)
    return "break"

def undo_text(event):
    # Simple undo: remove last added character (basic version)
    entry = event.widget
    text = entry.get()
    if text:
        entry.delete(len(text) - 1, tk.END)
    return "break"

root = tk.Tk()
original_geometry = root.geometry()
root.title("Mini Blitzme")
root.attributes("-topmost", True)  # App always stays on top
exit_button = tk.Button(root, text="⬅ Back", command=toggle_compact_mode)

# Task-related frame (will be hidden in compact mode)
task_frame = tk.Frame(root)
task_frame.pack(padx=10, pady=10)

task_listbox = tk.Listbox(task_frame, width=40)
task_listbox.pack()

btn_add = tk.Button(task_frame, text="Add Task", command=add_task)
btn_add.pack(pady=5)

btn_timer = tk.Button(task_frame, text="Start Timer", command=start_timer)
btn_timer.pack(pady=5)

btn_reset = tk.Button(task_frame, text="Reset All Tasks", command=reset_tasks)
btn_reset.pack(pady=5)

# Frame to hold the timer (visible in both modes)
frame = tk.Frame(root)
frame.pack()

timer_label = tk.Label(frame, text="00:00", font=("Arial", 14))
timer_label.pack(pady=5)

# Button to exit compact mode (initially hidden)
exit_button = tk.Button(root, text="⬅ Back", command=toggle_compact_mode)
finish_button = tk.Button(root, text="✔ Finish Early", command=lambda: stop_timer_early())

task_listbox.bind("<Button-3>", show_context_menu)

dark_mode = False  # default to light mode
dark_mode_btn = tk.Button(root, text="🌙 Dark Mode", command=toggle_dark_mode)
dark_mode_btn.pack(pady=5)

# Keyboard Shortcuts
root.bind("<Control-n>", lambda e: add_task())
root.bind("<Control-s>", lambda e: start_timer())
root.bind("<Control-f>", lambda e: stop_timer_early())  # Stop early manually
root.bind("<Control-r>", lambda e: reset_tasks())
root.bind("<Control-d>", lambda e: delete_task())
root.bind("<Control-b>", lambda e: toggle_compact_mode())
root.bind("<Control-BackSpace>", delete_word)
root.bind("<Control-z>", undo_text)
task_listbox.bind("<Delete>", lambda e: delete_task())

load_tasks()
update_list()

# Context menu setup
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="✔ Mark as Done", command=lambda: context_action("toggle"))
context_menu.add_command(label="✏ Rename", command=lambda: context_action("rename"))
context_menu.add_command(label="❌ Delete", command=lambda: context_action("delete"))

root.mainloop()
