import pandas as pd
import numpy  as np
import os
from scipy.optimize import linear_sum_assignment

def pick_csv(prompt):
    # List all csv files in the current directory, and lets the user pick
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in this folder! Please add your files and try again.")
        exit()

    print(f"\n--- {prompt} ---")
    for i, file in enumerate(csv_files):
        print(f"[{i + 1}] {file}")
    
    while True:
        try:
            choice = int(input("Select a file number: "))
            if 1 <= choice <= len(csv_files):
                return csv_files[choice - 1]
            print(f"Please enter a number between 1 and {len(csv_files)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def run_assignment():

    # Load data
    activities_file = pick_csv("Select your Activities Rules file")
    responses_file = pick_csv("Select your Student Responses file")

    print(f"\nUsing {activities_file} and {responses_file}")
    
    try:
        activities = pd.read_csv(activities_file)
        # Assume responses have 'Name' and 'Choice 1' columns
        students = pd.read_csv(responses_file).dropna(subset=['Name', 'Choice 1'])
    except Exception as e:
        print(f"Error reading files: {e}")
        return

    # Create slots
    slot_to_activity = []
    for _, row in activities.iterrows():
        for i in range(int(row['Max Capacity'])):
            slot_to_activity.append(row['Activity Name'])


    num_students = len(students)
    num_slots = len(slot_to_activity)

    # Cost Matrix uses 1,000,000 cost for unranked activities
    UNRANKED_COST = 1_000_000
    cost_matrix = np.full((num_students, num_slots), UNRANKED_COST)

    # Map weights to choice number
    choice_cols = [c for c in students.columns if 'Choice' in c]

    activity_to_slot_indices = {}
    for idx, act_name in enumerate(slot_to_activity):
        if act_name not in activity_to_slot_indices:
            activity_to_slot_indices[act_name] = []
        activity_to_slot_indices[act_name].append(idx)

    for i, student in students.reset_index().iterrows():
        for col in choice_cols:
            if pd.isna(student[col]): continue # Skip if student didn't fill all slots
            
            choice_num = int(''.join(filter(str.isdigit, col)))
            cost = choice_num ** 2
            pref = str(student[col]).strip()

            # Assign cost to all slots of the preferred activity
            if pref in activity_to_slot_indices:
                for slot_idx in activity_to_slot_indices[pref]:
                    cost_matrix[i, slot_idx] = cost

    # Use Munkres Algorithm
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Export to new file
    final_results = []
    for i, j in zip(row_ind, col_ind):
        cost_val = cost_matrix[i, j]
        final_results.append({
            'Student Name': students.iloc[i]['Name'],
            'Assigned Activity': slot_to_activity[j],
            'Choice Rank': "Unranked" if cost_val == UNRANKED_COST else f"Choice {int(np.sqrt(cost_val))}"
        })

    output_df = pd.DataFrame(final_results)
    output_df.to_csv('final_assignments.csv', index=False)

    print(output_df['Choice Rank'].value_counts().sort_index())


if __name__ == "__main__":
    run_assignment()