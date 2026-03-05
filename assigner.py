import pandas as pd
import numpy as np
import os
from scipy.optimize import linear_sum_assignment

def pick_csv(prompt):
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files:
        print("[ERROR] No CSV files found in this folder!")
        exit()
    print(f"\n--- {prompt} ---")
    for i, file in enumerate(csv_files):
        print(f"[{i + 1}] {file}")
    while True:
        try:
            choice = int(input("Select a file number: "))
            if 1 <= choice <= len(csv_files):
                return csv_files[choice - 1]
        except ValueError: pass
        print("Invalid input.")

def run_assignment():
    # Load data
    activities_file = pick_csv("Select Activities file")
    responses_file = pick_csv("Select Responses file")
    
    try:
        activities = pd.read_csv(activities_file)
        students = pd.read_csv(responses_file).dropna(subset=['Name', 'Choice 1'])
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    # Create initial slots
    slot_to_activity = []
    for _, row in activities.iterrows():
        for i in range(int(row['Max Capacity'])):
            slot_to_activity.append(row['Activity Name'])

    num_students = len(students)
    num_physical_slots = len(slot_to_activity)

    # Warn the user when there are too many students, but create "phantom" slots
    num_waitlist = 0
    if num_students > num_physical_slots:
        num_waitlist = num_students - num_physical_slots
        print(f"\n[WARNING]: {num_students} students vs {num_physical_slots} slots.")
        print(f"-> {num_waitlist} students will be assigned to 'WAITLIST'.")
        
        # Add the "phantom" names to our slot list
        for _ in range(num_waitlist):
            slot_to_activity.append("UNASSIGNED")

    # Create cost matrix
    UNRANKED_COST = 1_000_000 # High cost so students don't get unranked options
    WAITLIST_COST = 5_000_000 # Higher than unranked so it's the absolute last resort
    
    num_total_slots = len(slot_to_activity)
    cost_matrix = np.full((num_students, num_total_slots), UNRANKED_COST)

    # Set Waitlist columns to the super high cost
    if num_waitlist > 0:
        cost_matrix[:, -num_waitlist:] = WAITLIST_COST

    # Map weight
    choice_cols = [c for c in students.columns if 'Choice' in c]
    activity_to_slots = {}
    for idx, name in enumerate(slot_to_activity):
        if name != "WAITLIST / UNASSIGNED": # Don't map choices to the waitlist
            activity_to_slots.setdefault(name, []).append(idx)

    
    for i, student in students.reset_index().iterrows():
        for col in choice_cols:
            if pd.isna(student[col]): 
                continue
            
            # Extract digits to get the choice number (e.g., 'Choice 1' -> 1)
            digits = ''.join(filter(str.isdigit, col))
            
            if not digits:
                # Skip columns like 'Choice' that have no number
                continue
                
            choice_num = int(digits)
            cost = choice_num ** 2
            pref = str(student[col]).strip()

            # Assign cost to the correct activity slots
            if pref in activity_to_slots:
                for slot_idx in activity_to_slots[pref]:
                    cost_matrix[i, slot_idx] = cost

    # Use Munkres Algorithm
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Export to new file
    final_results = []
    for i, j in zip(row_ind, col_ind):
        cost_val = cost_matrix[i, j]
        
        # Logic for determining the Rank label
        if cost_val == WAITLIST_COST:
            rank_label = "No Room Available"
        elif cost_val == UNRANKED_COST:
            rank_label = "Unranked Activity"
        else:
            rank_label = f"Choice {int(np.sqrt(cost_val))}"

        final_results.append({
            'Student Name': students.iloc[i]['Name'],
            'Assigned Activity': slot_to_activity[j],
            'Outcome': rank_label
        })

    pd.DataFrame(final_results).to_csv('final_assignments.csv', index=False)
    output_df = pd.DataFrame(final_results)
    print("\n--- Final Assignment Summary ---")
    print(output_df['Outcome'].value_counts().to_frame('Total Students'))
    print("\nDone! Results in 'final_assignments.csv'")

if __name__ == "__main__":
    run_assignment()
