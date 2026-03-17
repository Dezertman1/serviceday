import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from scipy.optimize import linear_sum_assignment
import re

#  Palette 
BG        = "#F7F8FA"
CARD      = "#FFFFFF"
BORDER    = "#E2E5EA"
PRIMARY   = "#2563EB"
PRIMARY_H = "#1D4ED8"
SUCCESS   = "#16A34A"
TEXT      = "#111827"
SUBTEXT   = "#6B7280"
TAG_COLS  = {
    "Choice 1":          ("#DCFCE7", "#15803D"),
    "Choice 2":          ("#DBEAFE", "#1D4ED8"),
    "Choice 3":          ("#EDE9FE", "#6D28D9"),
    "Choice 4":          ("#F3E8FF", "#7E22CE"),
    "Choice 5":          ("#FFF7ED", "#C2410C"),
    "Unranked Activity": ("#FEF9C3", "#854D0E"),
    "No Choice Possible":("#FEE2E2", "#B91C1C"),
}

FONT_TITLE  = ("Helvetica Neue", 18, "bold")
FONT_LABEL  = ("Helvetica Neue", 10)
FONT_BUTTON = ("Helvetica Neue", 10, "bold")
FONT_MONO   = ("Courier", 9)

#  When I add the attendance question to my form, set these two values
ATTENDANCE_COLUMN        = "Which of the following best answers your attendence plan on Service Day.  (Friday, May 8)"   # e.g. "Will you attend Service Day?"
ATTENDANCE_CONFIRM_VALUE = "Can't wait!  Please give me one of my top choices if possible!"   # e.g. "Yes"

RANK_MAP = {
    "1st Request": 1, "2nd Request": 2, "3rd Request": 3,
    "4th Request": 4, "5th Request": 5,
}


def load_activities(path):
    df = pd.read_csv(path)
    cols = df.columns.tolist()

    # Detect and rename to a standard schema
    name_col = next((c for c in cols if c.strip().lower() in
                     ("activity name", "project name")), None)
    cap_col  = next((c for c in cols if c.strip().lower() in
                     ("max capacity", "maximu students", "maximum students",
                      "max students")), None)

    if not name_col or not cap_col:
        raise ValueError(
            f"Could not find activity name / capacity columns.\n"
            f"Found: {cols}\n"
            f"Expected one of: 'Activity Name', 'Project Name'\n"
            f"and one of: 'Max Capacity', 'Maximu Students', 'Maximum Students'"
        )

    df = df[[name_col, cap_col]].copy()
    df.columns = ["Activity Name", "Max Capacity"]
    df["Activity Name"] = df["Activity Name"].str.strip()
    df["Max Capacity"]  = pd.to_numeric(df["Max Capacity"], errors="coerce").fillna(0).astype(int)
    return df


def parse_responses(path):
    df = pd.read_csv(path)
    cols = df.columns.tolist()

    fname_col = next((c for c in cols if "first name" in c.lower()), None)
    lname_col = next((c for c in cols if "last name" in c.lower()), None)

    if fname_col and lname_col:
        df["Name"] = df[lname_col].str.strip().fillna("") + ", " + df[fname_col].str.strip().fillna("")
    else:
        name_col = next((c for c in cols if "name" in c.lower()), None)
        df["Name"] = df[name_col] if name_col else "Unknown Student"

    proj_cols = [c for c in df.columns if "Project Requests." in c and "[" in c]

    def extract_activity(col):
        m = re.search(r"\[(.+?)\]", col)
        return m.group(1).strip() if m else col

    prefs = []
    for _, row in df.iterrows():
        choices = {}
        for col in proj_cols:
            val = str(row[col]).strip() if pd.notna(row[col]) else ""
            rank = RANK_MAP.get(val)
            if rank:
                choices[rank] = extract_activity(col)
        prefs.append(choices)
    df["_prefs"] = prefs

    if ATTENDANCE_COLUMN and ATTENDANCE_COLUMN in df.columns:
        df["_will_attend"] = (df[ATTENDANCE_COLUMN].astype(str).str.strip()
                              == str(ATTENDANCE_CONFIRM_VALUE))
    else:
        df["_will_attend"] = True

    return df[["Name", "_prefs", "_will_attend"]].reset_index(drop=True)


class AssignerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Service Day Assignment")
        self.root.geometry("780x640")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.activities_path = tk.StringVar()
        self.student_path    = tk.StringVar()

        self._build_header()
        self._build_file_card()
        self._build_run_button()
        self._build_results_card()

    #  Header 
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(22, 4))
        tk.Label(hdr, text="Service Day", font=FONT_TITLE,
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(hdr, text="  Assignment Tool", font=("Helvetica Neue", 18),
                 bg=BG, fg=SUBTEXT).pack(side="left")
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(6, 0))

    #  File card 
    def _build_file_card(self):
        card = tk.Frame(self.root, bg=CARD, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=28, pady=14)
        tk.Label(card, text="DATA SOURCES", font=("Helvetica Neue", 8, "bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w", padx=16, pady=(12, 6))
        self._file_row(card, "Activities CSV", self.activities_path, self._load_activities)
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16)
        self._file_row(card, "Responses CSV",  self.student_path,    self._load_students)

    def _file_row(self, parent, label, var, cmd):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=16, pady=8)
        tk.Label(row, text=label, font=FONT_LABEL, bg=CARD,
                 fg=TEXT, width=14, anchor="w").pack(side="left")
        pill = tk.Frame(row, bg=BG, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        pill.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(pill, textvariable=var, font=FONT_MONO, bg=BG,
                 fg=SUBTEXT, anchor="w", padx=8, pady=4).pack(fill="x")
        tk.Button(row, text="Browse", font=FONT_BUTTON,
                  bg=PRIMARY, fg="white", relief="flat",
                  activebackground=PRIMARY_H, activeforeground="white",
                  cursor="hand2", padx=14, pady=4, command=cmd).pack(side="right")
    #  Run button 
    def _build_run_button(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="x", padx=28, pady=4)
        self.run_button = tk.Button(
            frame, text="▶  Run Assignment",
            font=FONT_BUTTON, bg=SUCCESS, fg="white",
            relief="flat", activebackground="#15803D",
            activeforeground="white", cursor="hand2",
            padx=20, pady=10, command=self.process_logic)
        self.run_button.pack(side="right")

    #  Results card 
    def _build_results_card(self):
        card = tk.Frame(self.root, bg=CARD, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True, padx=28, pady=(4, 20))
        tk.Label(card, text="RESULTS SUMMARY", font=("Helvetica Neue", 8, "bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w", padx=16, pady=(12, 6))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background=CARD, fieldbackground=CARD,
                        foreground=TEXT, rowheight=32,
                        font=FONT_LABEL, borderwidth=0)
        style.configure("Custom.Treeview.Heading",
                        background=BG, foreground=SUBTEXT,
                        font=("Helvetica Neue", 9, "bold"),
                        relief="flat", borderwidth=0)
        style.map("Custom.Treeview",
                  background=[("selected", "#EFF6FF")],
                  foreground=[("selected", TEXT)])
        style.map("Custom.Treeview.Heading", relief=[("active", "flat")])

        cols = ("Outcome", "Count", "Percentage")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 style="Custom.Treeview", selectmode="none")
        self.tree.heading("Outcome",    text="Outcome")
        self.tree.heading("Count",      text="Students")
        self.tree.heading("Percentage", text="Share")
        self.tree.column("Outcome",    width=220, anchor="w")
        self.tree.column("Count",      width=90,  anchor="center")
        self.tree.column("Percentage", width=90,  anchor="center")

        sb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        sb.pack(side="right", fill="y", pady=(0, 12), padx=(0, 8))

        for tag, (bg, fg) in TAG_COLS.items():
            self.tree.tag_configure(tag, background=bg, foreground=fg)

        self.placeholder = tk.Label(card,
            text="Run an assignment to see results here.",
            font=FONT_LABEL, bg=CARD, fg=SUBTEXT)
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

    #  File loaders 
    def _load_activities(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path: self.activities_path.set(path)

    def _load_students(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path: self.student_path.set(path)

    #  Core logic 
    def process_logic(self):
        if not self.activities_path.get() or not self.student_path.get():
            messagebox.showerror("Error", "Please select both .CSV files.")
            return

        # Ask the user where to save the file BEFORE running the logic
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="final_assignments.csv",
            title="Save Assignments As"
        )
        
        # If user cancels the save dialog
        if not save_path:
            return

        try:
            # Data Loading & Parsing
            activities_df = load_activities(self.activities_path.get())
            students_df = parse_responses(self.student_path.get())

            # Filter for only those attending
            students_df = students_df[students_df["_will_attend"]].reset_index(drop=True)
            
            # Create Slots
            slot_to_activity = []
            for _, row in activities_df.iterrows():
                for _ in range(int(row['Max Capacity'])):
                    slot_to_activity.append(row['Activity Name'])

            num_students = len(students_df)
            num_physical_slots = len(slot_to_activity)

            # Handle Overflow (Waitlist)
            num_waitlist = 0
            if num_students > num_physical_slots:
                num_waitlist = num_students - num_physical_slots
                for _ in range(num_waitlist):
                    slot_to_activity.append("WAITLIST / UNASSIGNED")

            # Setup Cost Matrix
            UNRANKED_COST = 1_000_000
            WAITLIST_COST = 5_000_000
            num_total_slots = len(slot_to_activity)
            cost_matrix = np.full((num_students, num_total_slots), UNRANKED_COST)
            
            if num_waitlist > 0: 
                cost_matrix[:, -num_waitlist:] = WAITLIST_COST

            activity_to_slots = {}
            for i, name in enumerate(slot_to_activity):
                if name != "WAITLIST / UNASSIGNED":
                    activity_to_slots.setdefault(name, []).append(i)

            WILDCARD_ACTIVITY = "Happy to help wherever needed!"
            UNRANKED_COST = 1_000_000
            WAITLIST_COST = 5_000_000

            # Pass 1 - Fill choice 1 at the start
            locked = {}  # student_index -> slot_index
            slot_used = set()

            for i, student in students_df.iterrows():
                first_choice = student["_prefs"].get(1)
                if first_choice and first_choice in activity_to_slots:
                    # Find a free slot for this activity
                    for slot_idx in activity_to_slots[first_choice]:
                        if slot_idx not in slot_used:
                            locked[i] = slot_idx
                            slot_used.add(slot_idx)
                            break
                        
            # Pass 2 - assign remaining students
            remaining_students = [i for i in range(num_students) if i not in locked]
            remaining_slots = [j for j in range(num_total_slots) if j not in slot_used]

            final_results = []

            # Add locked students to results first
            import math
            for i, j in locked.items():
                final_results.append({
                    'Name': students_df.iloc[i]['Name'],
                    'Assigned Activity': slot_to_activity[j],
                    'Outcome': 'Choice 1'
                })

            if remaining_students and remaining_slots:
                n_rem_s = len(remaining_students)
                n_rem_sl = len(remaining_slots)

                # Pad slots if too many students
                extra_waitlist = 0
                if n_rem_s > n_rem_sl:
                    extra_waitlist = n_rem_s - n_rem_sl
                    remaining_slots += [-1] * extra_waitlist  # waitlist slots
                    n_rem_sl = len(remaining_slots)

                cost_matrix2 = np.full((n_rem_s, n_rem_sl), UNRANKED_COST)

                for new_i, orig_i in enumerate(remaining_students):
                    prefs = students_df.iloc[orig_i]["_prefs"]
                    for rank, act_name in prefs.items():
                        if rank == 1:
                            continue  # Skip if choice 1 fails from capacity
                        if act_name == WILDCARD_ACTIVITY:
                            # Wildcard at rank 2+: use normal cost but find its remaining slots
                            cost = 10 ** (int(rank) - 1)
                        else:
                            cost = 10 ** (int(rank) - 1)
                        if act_name in activity_to_slots:
                            for slot_idx in activity_to_slots[act_name]:
                                if slot_idx in remaining_slots:
                                    new_j = remaining_slots.index(slot_idx)
                                    cost_matrix2[new_i, new_j] = cost

                    # Wildcard rank 1 that didn't get locked forces to 0 on any wildcard slot
                    if prefs.get(1) == WILDCARD_ACTIVITY and WILDCARD_ACTIVITY in activity_to_slots:
                        for slot_idx in activity_to_slots[WILDCARD_ACTIVITY]:
                            if slot_idx in remaining_slots:
                                new_j = remaining_slots.index(slot_idx)
                                cost_matrix2[new_i, new_j] = 0

                    # Waitlist placeholder slots
                    for wl_offset in range(extra_waitlist):
                        cost_matrix2[new_i, n_rem_sl - extra_waitlist + wl_offset] = WAITLIST_COST

                row_ind2, col_ind2 = linear_sum_assignment(cost_matrix2)

                for new_i, new_j in zip(row_ind2, col_ind2):
                    orig_i = remaining_students[new_i]
                    slot_idx = remaining_slots[new_j]
                    cost_val = cost_matrix2[new_i, new_j]

                    if cost_val == WAITLIST_COST or slot_idx == -1:
                        label = "No Choice Possible"
                        activity = "WAITLIST / UNASSIGNED"
                    elif cost_val == UNRANKED_COST:
                        label = "Unranked Activity"
                        activity = slot_to_activity[slot_idx]
                    elif cost_val == 0:
                        label = "Choice 1"
                        activity = slot_to_activity[slot_idx]
                    else:
                        rank = int(math.log10(cost_val)) + 1
                        label = f"Choice {rank}"
                        activity = slot_to_activity[slot_idx]

                    final_results.append({
                        'Name': students_df.iloc[orig_i]['Name'],
                        'Assigned Activity': activity,
                        'Outcome': label
                    })

            # Save to the user-selected path
            output_df = pd.DataFrame(final_results)
            output_df.to_csv(save_path, index=False)

            for item in self.tree.get_children():
                self.tree.delete(item)

            stats = output_df['Outcome'].value_counts()
            total = len(output_df)
            for label, count in stats.items():
                percentage = (count / total) * 100
                self.tree.insert("", "end", values=(label, count, f"{percentage:.1f}%"))

            messagebox.showinfo("Success", f"Assignments saved to:\n{save_path}")

        except Exception as e:
            messagebox.showerror("Runtime Error", f"Something went wrong:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app  = AssignerApp(root)
    root.mainloop()