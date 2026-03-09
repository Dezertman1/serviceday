import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from scipy.optimize import linear_sum_assignment
import os

# Palette
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
    "Unranked Activity": ("#FEF9C3", "#854D0E"),
    "No Choice Possible":("#FEE2E2", "#B91C1C"),
}

FONT_TITLE  = ("Helvetica Neue", 18, "bold")
FONT_LABEL  = ("Helvetica Neue", 10)
FONT_SMALL  = ("Helvetica Neue", 9)
FONT_BUTTON = ("Helvetica Neue", 10, "bold")
FONT_MONO   = ("Courier", 9)


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

    # Header
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(22, 4))
        tk.Label(hdr, text="Service Day", font=FONT_TITLE,
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(hdr, text="  Assignment Tool", font=("Helvetica Neue", 18),
                 bg=BG, fg=SUBTEXT).pack(side="left")
        rule = tk.Frame(self.root, bg=BORDER, height=1)
        rule.pack(fill="x", padx=28, pady=(6, 0))

    # File card
    def _build_file_card(self):
        card = tk.Frame(self.root, bg=CARD, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=28, pady=14)
        tk.Label(card, text="DATA SOURCES", font=("Helvetica Neue", 8, "bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w", padx=16, pady=(12, 6))
        self._file_row(card, "Activities CSV", self.activities_path, self.load_activities)
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16)
        self._file_row(card, "Responses CSV",  self.student_path,    self.load_students)

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

    # Run button
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

    # Results card 
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

    # File loaders 
    def load_activities(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path: self.activities_path.set(path)

    def load_students(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path: self.student_path.set(path)

    # Core logic 
    def process_logic(self):
        if not self.activities_path.get() or not self.student_path.get():
            messagebox.showerror("Error", "Please select both CSV files.")
            return
        try:
            activities = pd.read_csv(self.activities_path.get())
            students   = pd.read_csv(self.student_path.get()).dropna(
                             subset=["Name", "Choice 1"])

            slot_to_activity = []
            for _, row in activities.iterrows():
                for _ in range(int(row["Max Capacity"])):
                    slot_to_activity.append(row["Activity Name"])

            num_students       = len(students)
            num_physical_slots = len(slot_to_activity)
            num_waitlist       = 0
            if num_students > num_physical_slots:
                num_waitlist = num_students - num_physical_slots
                slot_to_activity += ["WAITLIST / UNASSIGNED"] * num_waitlist

            UNRANKED_COST   = 1_000_000
            WAITLIST_COST   = 5_000_000
            num_total_slots = len(slot_to_activity)
            cost_matrix     = np.full((num_students, num_total_slots), UNRANKED_COST)
            if num_waitlist > 0:
                cost_matrix[:, -num_waitlist:] = WAITLIST_COST

            activity_to_slots = {}
            for i, name in enumerate(slot_to_activity):
                if name != "WAITLIST / UNASSIGNED":
                    activity_to_slots.setdefault(name, []).append(i)

            choice_cols = [c for c in students.columns if "Choice" in c]
            for i, student in students.reset_index().iterrows():
                for col in choice_cols:
                    if pd.isna(student[col]): continue
                    digits = "".join(filter(str.isdigit, col))
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
                label = ("No Choice Possible" if cost_val == WAITLIST_COST else
                         "Unranked Activity"  if cost_val == UNRANKED_COST  else
                         f"Choice {int(np.sqrt(cost_val))}")
                final_results.append({
                    "Name":     students.iloc[i]["Name"],
                    "Activity": slot_to_activity[j],
                    "Outcome":  label,
                })

            df = pd.DataFrame(final_results)
            out_path = os.path.join(
                os.path.dirname(self.student_path.get()), "final_assignments.csv")
            df.to_csv(out_path, index=False)

            for item in self.tree.get_children():
                self.tree.delete(item)
            self.placeholder.place_forget()

            order = ["Choice 1","Choice 2","Choice 3","Unranked Activity","No Choice Possible"]
            stats = df["Outcome"].value_counts()
            stats = stats.reindex(
                [o for o in order if o in stats.index] +
                [o for o in stats.index if o not in order])
            total = len(df)
            for outcome, count in stats.items():
                pct = (count / total) * 100
                tag = outcome if outcome in TAG_COLS else ""
                self.tree.insert("", "end",
                                 values=(outcome, count, f"{pct:.1f}%"),
                                 tags=(tag,))

            messagebox.showinfo("Done",
                f"Assignment complete!\nSaved to:\n{out_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app  = AssignerApp(root)
    root.mainloop()