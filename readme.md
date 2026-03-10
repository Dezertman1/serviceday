# Service Day Assignment Tool

## Overview

This tool uses the Hungarian Algorithm to assign students to their chosen activities.

---

## Requirements

- Python 3.8+
- The following Python packages:
  - `pandas`
  - `numpy`
  - `scipy`
  - `tkinter`

Install dependencies with:

```bash
pip install pandas numpy scipy
```

---

## Run

```bash
python assigner_gui.py
```

---

## Input Files

The tool takes two CSV files as input.

### 1. Activities CSV (Master List)

Contains the list of projects and their maximum student capacity.

**Accepted column names:**

| Purpose | Accepted Names |
|---|---|
| Project name | `Activity Name` or `Project Name` |
| Capacity | `Max Capacity`, or `Maximum Students` |

**Example:**

```
Project Name,Maximum Students
Berlin Lake Trail,40
Blanket Builders,12
Cooks in the Kitchen,10
```

### 2. Responses CSV (Google Form Export)

Exported directly from Google Forms. The tool expects:

- A `First Name` and `Last Name` column
- Project preference columns in the format `Project Requests [Activity Name]` with values `1st Request` through `5th Request`

**Example columns:**

```
First Name, Last Name, Project Requests [Berlin Lake Trail], Project Requests [Palmyra Park], ...
```

---

## Attendance Column

When the question is added to the form for student attendance, add the corresponding to the top of `assigner_gui.py`:

```python
ATTENDANCE_COLUMN        = "Will you attend Service Day?"  # column name
ATTENDANCE_CONFIRM_VALUE = "Yes"                           # answer
```

Students who do not match the confirming value will still be assigned, but only after all confirmed attendees have been placed first.

---

## Output Files

Both files are saved to the same folder as your responses CSV.

### `final_assignments.csv`

One row per student with three columns:

| Column | Description |
|---|---|
| `Name` | Student name in `Last, First` format |
| `Activity` | Assigned project |
| `Outcome` | `Choice 1` – `Choice 5`, `Unranked Activity`, or `No Choice Possible` |

---

## Outcome Definitions

| Outcome | Meaning |
|---|---|
| `Choice 1 - 5` | Student was assigned one of their ranked preferences |
| `Unranked Activity` | Student was assigned a project they did not rank, all their preferred projects were full |
| `No Choice Possible` | There were more students than total available slots; student is put on the waitlist |

---

## Results Summary 

After running, the app displays a summary table:

| Colour | Outcome |
|---|---|
| Green | Choice 1 |
| Blue | Choice 2 |
| Purple | Choice 3 |
| Yellow | Unranked Activity |
| Red | No Choice Possible |

---

Each student–project slot pair is assigned a **cost** based on the student's ranking: `rank²` (so 1st choice = 1, 2nd = 4, 3rd = 9, etc.). Squaring the rank penalises lower choices more heavily, pushing the algorithm to prioritise top choices. Projects the student did not rank are given a high cost (`1,000,000`) so the algorithm only assigns them there as a last resort. If there are more students than slots, phantom "waitlist" slots are added with an even higher cost (`5,000,000`) so real slots are always preferred.

---

## Packaging as Executable (PyInstaller)

To package as an executable, run:

```bash
pyinstaller --onefile --windowed \
  --hidden-import=scipy.optimize \
  --hidden-import=scipy._lib.messagestream \
  --hidden-import=pandas \
  --hidden-import=numpy \
  assigner_gui.py
```

The compiled executable will appear in the `dist/` folder. Then use:

- `dist/assigner_gui.exe` (Windows) or `dist/assigner_gui` (macOS/Linux)

No other files are needed. The user selects their own CSV files at runtime via the Browse buttons.


---

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `No columns to parse from file` | Clicked Start before selecting both files, or selected the wrong file | Re-select files and ensure neither path is empty |
| `Unranked Activity` for many students | Project names in the form don't match the master list | Check `ACTIVITY_NAME_MAP` and add any missing mappings |
| Student missing from output | All their ranked choices were discontinued projects | They will appear in `dropped_students.csv` |
| `Runtime Error: Something went wrong` | Unexpected CSV format | Ensure column names match the expected formats listed above |