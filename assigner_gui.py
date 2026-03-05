import pandas as pd
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from scipy.optimize import linear_sum_assignment

class AssignerApp:
    def __init__(self, root):
        self.root = root
        self.root.title = "Service Day Assignment"
        self.root.geometry("600x650")

        self.activities_path = tk.StringVar()
        self.students_path = tk.StringVar()

        tk.Label(root, text="Service Day Assignment", font=("Arial", 16, "bold"))

        # File Selection Frame
        file_frame = tk.LabelFrame(root, text="Select Data Sources", padx=10, pady=10)
        file_frame.pack(fill="x", padx=20, pady=10)

        tk.Button(file_frame, text="Browse Activities CSV", command=self.load_activities).grid(row=0, column=0, pady=5)
        tk.Label(file_frame, textvariable=self.activities_path, fg="blue", wraplength=400).grid(row=0, column=1, padx=10)

        tk.Button(file_frame, text="Browse Responses CSV", command=self.load_responses).grid(row=1, column=0, pady=5)
        tk.Label(file_frame, textvariable=self.responses_path, fg="blue", wraplength=400).grid(row=1, column=1, padx=10)

        # Action Button
        self.run_button = tk.Button(root, text="Start", bg="#4CAF50", fg="white", 
                                font=("Arial", 12, "bold"), height=2, command=self.process_logic)
        self.run_button.pack(pady=15)

        # Results Frame
        self.results_frame = tk.LabelFrame(root, text="Assignment Summary")
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Treeview
        self.tree = ttk.Treeview(self.results_frame, columns=("Rank", "Count", "Percentage"), show='headings')
        self.tree.heading("Rank", text="Student Choice")
        self.tree.heading("Count", text="Number of Students")
        self.tree.heading("Percentage", text="% of Total")
        self.tree.column("Rank", width=150)
        self.tree.column("Count", width=80, anchor="center")
        self.tree.column("Percentage", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def load_activities(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path: self.activities_path.set(path)

    def load_students(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path: self.students_path_path.set(path)

    def process_logic(self):
        if not self.activities_path.get() or not self.students_path.get():
            messagebox.showerror("Error", "Please select both .CSV files.")

        # Logic
        try:
            activities = pd.read_csv(self.activities_path.get())
            students = pd.read_csv(self.responses_path.get()).dropna(subset=['Name', 'Choice 1'])

            slot_to_activity = []
            for _, row in activities.iterrows():
                for i in range(int(row['Max Capacity'])):
                    slot_to_activity.append(row['Activity Name'])

            num_students = len(students)
            num_physical_slots = len(slot_to_activity)

            # Phantom Slots
            num_waitlist = 0
            if num_students > num_physical_slots:
                num_waitlist = num_students - num_physical_slots
                for _ in range(num_waitlist):
                    slot_to_activity.append("WAITLIST / UNASSIGNED")

            UNRANKED_COST = 1_000_000
            WAITLIST_COST = 5_000_000
            num_total_slots = len(slot_to_activity)
            cost_matrix = np.full((num_students, num_total_slots), UNRANKED_COST)
            if num_waitlist > 0: cost_matrix[:, -num_waitlist:] = WAITLIST_COST

            activity_to_slots = {}
            for i, name in enumerate(slot_to_activity):
                if name != "WAITLIST / UNASSIGNED":
                    activity_to_slots.setdefault(name, []).append(i)

            choice_cols = [c for c in students.columns if 'Choice' in c]
            for i, student in students.reset_index().iterrows():
                for col in choice_cols:
                    if pd.isna(student[col]): continue
                    digits = ''.join(filter(str.isdigit, col))
                    if not digits: continue
                    cost = int(digits) ** 2
                    pref = str(student[col]).strip()
                    if pref in activity_to_slots:
                        for slot_idx in activity_to_slots[pref]:
                            cost_matrix[i, slot_idx] = cost

            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            final_results = []
            for i, j in zip(row_ind, col_ind):
                cost_val = cost_matrix[i, j]
                label = "No Choice Possible" if cost_val == WAITLIST_COST else \
                        "Unranked Activity" if cost_val == UNRANKED_COST else \
                        f"Choice {int(np.sqrt(cost_val))}"
                
                final_results.append({'Outcome': label, 'Name': students.iloc[i]['Name'], 'Activity': slot_to_activity[j]})