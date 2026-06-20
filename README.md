FastBox Mystery Delivery System
Assignment: Python Developer Position — Nexgensis Technologies Pvt. Ltd.
Candidate submission | Due: 27 May 2026, 12:00 PM

Overview
This project simulates one day of operations for FastBox, a fictional delivery company. It reads a JSON input file describing warehouses, delivery agents, and packages; assigns packages to the nearest agent; simulates each delivery leg; and produces a structured JSON report.

Project Structure
fastbox_delivery/
├── delivery_system.py       # Core simulator (main module)
├── test_delivery_system.py  # Automated test runner
├── data/
│   └── base_case.json       # Provided base case input
├── test_cases/
│   ├── test_case_1.json     # 10 additional test cases
│   ├── test_case_2.json
│   └── ... (through test_case_10.json)
└── README.md                # This file
How to Run
Single simulation
python delivery_system.py data/base_case.json report.json
Output files: report.json, top_performer.csv

All test cases (automated)
python test_delivery_system.py
As a Python module
from delivery_system import run

report = run("data/base_case.json", report_path="report.json")
print(report)
No external dependencies required. Uses only Python 3 standard library.

Output Format
report.json:

{
  "A1": {"packages_delivered": 2, "total_distance": 85.32, "efficiency": 42.66},
  "A2": {"packages_delivered": 2, "total_distance": 120.12, "efficiency": 60.06},
  "A3": {"packages_delivered": 1, "total_distance": 50.00, "efficiency": 50.00},
  "best_agent": "A1"
}
top_performer.csv:

agent_id,packages_delivered,total_distance,efficiency
A1,2,85.32,42.66
Algorithm
1. JSON Parsing
The loader normalises two input formats automatically:

Dict format (test cases): {"warehouses": {"W1": [0, 0]}}
List format (base case): {"warehouses": [{"id": "W1", "location": [0, 0]}]}
2. Package Assignment
Each package is assigned to the nearest agent using Euclidean distance from the agent's initial position to the package's warehouse. All assignments use initial positions (one-pass greedy).

3. Delivery Simulation
Each agent travels: start → warehouse(p1) → dest(p1) → warehouse(p2) → dest(p2) → …

Legs are chained — the agent's position updates after each delivery so multi-package routes are realistic.

4. Report Generation
efficiency = total_distance / packages_delivered (average distance per package; lower = better)
best_agent = agent with the lowest efficiency score (≥1 package delivered)
Distances rounded to 2 decimal places
Assumptions & Design Decisions
All ambiguous scenarios are resolved as follows (documented per assignment instructions):

#	Scenario	Decision
1	Two input formats (dict vs list-of-dicts)	Both normalised automatically
2	Nearest-agent assignment — current or initial position?	Initial position (one-pass greedy)
3	Tie-breaking on equal distance	Lexicographically smaller agent ID (A1 < A2)
4	Delivery route for multi-package agent	Chained: start→W→D→W→D→…
5	Efficiency metric	total_distance / packages_delivered (lower = better)
6	Agents with zero packages	efficiency = null in report; not eligible for best_agent
7	Floating-point precision	All distances/efficiency rounded to 2 decimal places
Bonus Features Implemented
Random Delivery Delays — Seeded random delays (0–30 min per leg) added per agent; printed to console during simulation.
ASCII Route Visualisation — Each agent's delivery path rendered as a 2D ASCII grid map (printed to console).
Export Top Performer to CSV — Best agent's stats saved to top_performer.csv.
Evaluation Criteria Coverage
Criteria	Implementation
JSON parsing (10%)	Dual-format normalisation in load_data()
Distance calculation (20%)	euclidean() helper using math.sqrt
Agent-package assignment (25%)	assign_packages() — greedy nearest-agent
Simulation & report (25%)	simulate_deliveries() + build_report() + save_report()
Code clarity & comments (10%)	Docstrings, inline comments, assumption block at top
Bonus creativity (10%)	Delays, ASCII visualiser, CSV export
Python Version
Tested with Python 3.8+. No third-party packages required.
