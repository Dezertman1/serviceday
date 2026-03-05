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