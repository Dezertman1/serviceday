import pandas as pd
import numpy  as np

def run_assignment():

    # Load data
    try:
        activities = pd.read.csv('activities.csv')
        students = pd.read.csv('student_responses.csv').dropna(subset=['Name', 'Choice 1'])
    except FileNotFoundError as e:
        print(f"Error: Could not find {e.filename}. Make sure your CSVs are named correctly.")

    # Create slots
    slot_to_activity = []
    for _, row in activities.iterrows():
        for i in range(int(row['Max Capacity'])):
            slot_to_activity.append(row(['Activity Name']))


    students_num = len(students)
    activities_num = len(slot_to_activity)

    # Cost Matrix uses 999 cost for unranked activities
    cost_matrix = np.full((num_students, num_slots), 999)