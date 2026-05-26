"""
FastBox Mystery Delivery System Simulator
==========================================
Assignment: Python Developer Position — Nexgensis Technologies Pvt. Ltd.

This module simulates one day of operations for the fictional delivery company
FastBox. It reads a JSON input file (or dict), assigns packages to the nearest
delivery agent, simulates each delivery, and produces a structured report.

Assumptions (documented as required):
  1. INPUT FORMAT FLEXIBILITY — The test cases use {"warehouses": {"W1": [x, y]}}
     (dict of lists), while base_case.json uses a list-of-dicts format
     ({"warehouses": [{"id": "W1", "location": [x, y]}]}). Both are normalised
     automatically before processing.

  2. NEAREST-AGENT ASSIGNMENT — Distance is measured from the agent's CURRENT
     position to the package's warehouse (not to the destination). Assignments
     are resolved greedily in the order packages appear in the input list.
     After each assignment the agent's position is NOT updated between package
     assignments — all assignments are done from initial positions (one-pass
     greedy). This matches the straightforward reading of "assign each package
     to the nearest agent".

  3. TIE-BREAKING — When two agents are equidistant from a warehouse, the agent
     with the lexicographically smaller ID is preferred (e.g. A1 before A2).

  4. DELIVERY ROUTE — Each agent travels: start → warehouse → destination for
     every package assigned to them. Packages are delivered in the order they
     are assigned (input order). The agent's position advances after each
     delivery so subsequent package legs are chained realistically.
     Route for agent with N packages:
       start → W(p1) → dest(p1) → W(p2) → dest(p2) → ... → W(pN) → dest(pN)

  5. EFFICIENCY — Defined as total_distance / packages_delivered (average
     distance per package, lower = more efficient). The "best agent" is the
     one with the lowest efficiency score among agents who delivered at least
     one package. Tie-breaking: lexicographically smaller ID wins.

  6. AGENTS WITH ZERO PACKAGES — Included in the report with
     packages_delivered=0, total_distance=0.0, efficiency=null (None/null).
     They are not eligible for "best_agent".

  7. FLOATING POINT ROUNDING — All distances and efficiency values are rounded
     to 2 decimal places in the report for readability.
"""

import json
import math
import sys
import csv
from pathlib import Path
from typing import Union


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def euclidean(p1: list, p2: list) -> float:
    """Return the Euclidean distance between two 2-D points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# ---------------------------------------------------------------------------
# Input normalisation
# ---------------------------------------------------------------------------

def _normalise_warehouses(raw) -> dict:
    """
    Accept either:
      {"W1": [x, y], ...}           — dict of coordinate lists (test cases)
      [{"id": "W1", "location": [x, y]}, ...] — list of dicts (base_case)
    Returns a uniform dict: {"W1": [x, y], ...}
    """
    if isinstance(raw, dict):
        return {wid: list(loc) for wid, loc in raw.items()}
    # list-of-dicts
    return {w["id"]: list(w["location"]) for w in raw}


def _normalise_agents(raw) -> dict:
    """
    Accept either:
      {"A1": [x, y], ...}          — dict of coordinate lists (test cases)
      [{"id": "A1", "location": [x, y]}, ...] — list of dicts (base_case)
    Returns a uniform dict: {"A1": [x, y], ...}
    """
    if isinstance(raw, dict):
        return {aid: list(loc) for aid, loc in raw.items()}
    return {a["id"]: list(a["location"]) for a in raw}


def _normalise_packages(raw) -> list:
    """
    Accept packages where warehouse key is either "warehouse" or "warehouse_id".
    Returns a list of dicts with keys: id, warehouse_id, destination.
    """
    normalised = []
    for pkg in raw:
        wid = pkg.get("warehouse_id") or pkg.get("warehouse")
        normalised.append({
            "id": pkg["id"],
            "warehouse_id": wid,
            "destination": list(pkg["destination"]),
        })
    return normalised


def load_data(source: Union[str, Path, dict]) -> dict:
    """
    Load and normalise delivery data from a JSON file path or an in-memory dict.
    Returns a dict with keys: warehouses (dict), agents (dict), packages (list).
    """
    if isinstance(source, dict):
        raw = source
    else:
        with open(source, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

    return {
        "warehouses": _normalise_warehouses(raw["warehouses"]),
        "agents":     _normalise_agents(raw["agents"]),
        "packages":   _normalise_packages(raw["packages"]),
    }


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def assign_packages(agents: dict, warehouses: dict, packages: list) -> dict:
    """
    Greedy nearest-agent assignment (from initial positions, see Assumption 2).

    Returns:
        assignments: {agent_id: [pkg_dict, ...]}
    """
    # Initialise empty assignment list for every agent
    assignments = {aid: [] for aid in agents}

    for pkg in packages:
        warehouse_loc = warehouses[pkg["warehouse_id"]]

        # Find the agent closest to the package's warehouse
        # Assumption 3: lexicographic tie-break
        best_agent = min(
            agents.keys(),
            key=lambda aid: (
                euclidean(agents[aid], warehouse_loc),
                aid          # tie-break: smaller ID wins
            ),
        )
        assignments[best_agent].append(pkg)

    return assignments


def simulate_deliveries(agents: dict, warehouses: dict, assignments: dict) -> dict:
    """
    Simulate each agent travelling start → warehouse → destination for each
    assigned package (chained — agent position updates after each delivery).
    See Assumption 4.

    Returns:
        results: {
            agent_id: {
                "packages_delivered": int,
                "total_distance": float,
                "efficiency": float | None,
                "route": [(label, [x, y]), ...]   # full path for ASCII visualiser
            }
        }
    """
    results = {}

    for agent_id, pkgs in assignments.items():
        current_pos = list(agents[agent_id])   # mutable copy
        total_dist  = 0.0
        route       = [("START", list(current_pos))]

        for pkg in pkgs:
            warehouse_loc = warehouses[pkg["warehouse_id"]]
            dest_loc      = pkg["destination"]

            # Leg 1: current position → warehouse
            leg1 = euclidean(current_pos, warehouse_loc)
            total_dist  += leg1
            current_pos  = list(warehouse_loc)
            route.append((f"W({pkg['warehouse_id']})", list(current_pos)))

            # Leg 2: warehouse → destination
            leg2 = euclidean(current_pos, dest_loc)
            total_dist  += leg2
            current_pos  = list(dest_loc)
            route.append((f"D({pkg['id']})", list(current_pos)))

        n_delivered = len(pkgs)
        # Assumption 5: efficiency = average distance per package (None if 0)
        efficiency = round(total_dist / n_delivered, 2) if n_delivered > 0 else None

        results[agent_id] = {
            "packages_delivered": n_delivered,
            "total_distance":     round(total_dist, 2),
            "efficiency":         efficiency,
            "route":              route,
        }

    return results


def determine_best_agent(results: dict) -> str:
    """
    The best agent has the lowest efficiency score (avg distance per package).
    Only agents who delivered ≥1 package are eligible.
    Tie-break: lexicographically smaller ID (Assumption 5).
    Returns the agent ID string, or None if no deliveries occurred at all.
    """
    eligible = {
        aid: info for aid, info in results.items()
        if info["efficiency"] is not None
    }
    if not eligible:
        return None

    return min(
        eligible.keys(),
        key=lambda aid: (eligible[aid]["efficiency"], aid)
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_report(results: dict, best_agent: str) -> dict:
    """
    Assemble the final JSON-serialisable report dict.
    Route data is excluded from the report (it's used only by the visualiser).
    """
    report = {}
    for agent_id, info in sorted(results.items()):
        report[agent_id] = {
            "packages_delivered": info["packages_delivered"],
            "total_distance":     info["total_distance"],
            "efficiency":         info["efficiency"],
        }
    report["best_agent"] = best_agent
    return report


def save_report(report: dict, output_path: Union[str, Path] = "report.json") -> None:
    """Serialise the report to a JSON file with pretty-printing."""
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"[✓] Report saved → {output_path}")


# ---------------------------------------------------------------------------
# Bonus features
# ---------------------------------------------------------------------------

def export_top_performer_csv(report: dict, output_path: Union[str, Path] = "top_performer.csv") -> None:
    """
    Bonus: Export the best agent's stats to a CSV file.
    """
    best = report.get("best_agent")
    if best is None:
        print("[!] No best agent to export.")
        return

    stats = report[best]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["agent_id", "packages_delivered", "total_distance", "efficiency"])
        writer.writeheader()
        writer.writerow({
            "agent_id":          best,
            "packages_delivered": stats["packages_delivered"],
            "total_distance":     stats["total_distance"],
            "efficiency":         stats["efficiency"],
        })
    print(f"[✓] Top performer exported → {output_path}")


def ascii_route_map(agent_id: str, route: list, grid_size: int = 20) -> str:
    """
    Bonus: Render a simple ASCII map for an agent's delivery route.

    The 2-D coordinate space is projected onto a (grid_size × grid_size) grid.
    Symbols:
      S  — starting position
      W  — warehouse pickup
      D  — delivery destination
      .  — empty cell
    Connections between stops are shown with lowercase letters (a, b, c, …).
    """
    if not route:
        return ""

    # Find bounding box of all points
    all_x = [p[1][0] for p in route]
    all_y = [p[1][1] for p in route]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # Avoid division by zero for single-point routes
    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1

    def to_grid(coord):
        """Map real coordinate to grid cell (col, row)."""
        col = int((coord[0] - min_x) / span_x * (grid_size - 1))
        row = int((coord[1] - min_y) / span_y * (grid_size - 1))
        # Invert row so y-axis goes up
        row = (grid_size - 1) - row
        return col, row

    grid = [['.' for _ in range(grid_size)] for _ in range(grid_size)]

    # Draw straight lines between consecutive stops (Bresenham-like)
    for idx in range(len(route) - 1):
        c1 = to_grid(route[idx][1])
        c2 = to_grid(route[idx + 1][1])
        label = chr(ord('a') + (idx % 26))
        # Linear interpolation
        steps = max(abs(c2[0] - c1[0]), abs(c2[1] - c1[1]), 1)
        for s in range(1, steps):
            cx = c1[0] + int(round(s * (c2[0] - c1[0]) / steps))
            cy = c1[1] + int(round(s * (c2[1] - c1[1]) / steps))
            if grid[cy][cx] == '.':
                grid[cy][cx] = label

    # Place stop markers (overwrite path chars)
    for label, coord in route:
        col, row = to_grid(coord)
        if label.startswith("START"):
            grid[row][col] = 'S'
        elif label.startswith("W("):
            grid[row][col] = 'W'
        elif label.startswith("D("):
            grid[row][col] = 'D'

    # Build string
    lines = [f"  Route map for {agent_id} ({grid_size}×{grid_size} grid)"]
    lines.append("  " + "─" * grid_size)
    for row in grid:
        lines.append("  " + "".join(row))
    lines.append("  " + "─" * grid_size)
    lines.append("  Legend: S=start  W=warehouse  D=delivery  a,b,…=path segments")
    return "\n".join(lines)


def simulate_random_delay(agent_id: str, n_packages: int, seed: int = None) -> dict:
    """
    Bonus: Inject random delivery delays (0–30 min per leg) for realism.
    Uses a seeded random so results are reproducible.
    Returns a dict with total delay minutes and per-package delays.
    """
    import random
    rng = random.Random(seed if seed is not None else hash(agent_id))
    delays = []
    for i in range(n_packages * 2):   # 2 legs per package (to warehouse + to dest)
        delays.append(round(rng.uniform(0, 30), 1))
    return {
        "agent_id":         agent_id,
        "per_leg_delays":   delays,
        "total_delay_min":  round(sum(delays), 1),
    }


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def run(
    input_source: Union[str, Path, dict],
    report_path:  Union[str, Path] = "report.json",
    csv_path:     Union[str, Path] = "top_performer.csv",
    print_ascii:  bool = True,
    print_delays: bool = True,
) -> dict:
    """
    Full pipeline: load → assign → simulate → report → (bonus features).

    Parameters
    ----------
    input_source : file path or already-parsed dict
    report_path  : where to write report.json
    csv_path     : where to write top_performer.csv
    print_ascii  : if True, print ASCII route maps to stdout
    print_delays : if True, print simulated delay summaries

    Returns
    -------
    report : dict  (also written to report_path)
    """
    # 1. Load & normalise input
    data = load_data(input_source)
    warehouses = data["warehouses"]
    agents     = data["agents"]
    packages   = data["packages"]

    print(f"\n{'='*55}")
    print(f"  FastBox Delivery Simulator")
    print(f"{'='*55}")
    print(f"  Warehouses : {len(warehouses)}")
    print(f"  Agents     : {len(agents)}")
    print(f"  Packages   : {len(packages)}")
    print(f"{'='*55}\n")

    # 2. Assign packages → agents (greedy nearest-agent)
    assignments = assign_packages(agents, warehouses, packages)

    print("  Package Assignment:")
    for aid in sorted(assignments):
        pkg_ids = [p["id"] for p in assignments[aid]]
        print(f"    {aid} → {pkg_ids if pkg_ids else '(no packages)'}")

    # 3. Simulate deliveries
    results = simulate_deliveries(agents, warehouses, assignments)

    # 4. Determine best agent
    best_agent = determine_best_agent(results)

    # 5. Build & save report
    report = build_report(results, best_agent)
    save_report(report, report_path)

    # 6. Pretty-print report summary
    print("\n  Delivery Report:")
    for aid in sorted(report):
        if aid == "best_agent":
            continue
        r = report[aid]
        eff = f"{r['efficiency']:.2f}" if r['efficiency'] is not None else "N/A"
        print(f"    {aid}: delivered={r['packages_delivered']}  "
              f"dist={r['total_distance']:.2f}  efficiency={eff}")
    print(f"\n  🏆 Best Agent: {best_agent}")

    # ------------------------------------------------------------------
    # Bonus 1: Simulated random delays
    # ------------------------------------------------------------------
    if print_delays:
        print("\n  [Bonus] Simulated Delivery Delays:")
        for aid in sorted(assignments):
            n = len(assignments[aid])
            if n > 0:
                delay_info = simulate_random_delay(aid, n, seed=42)
                print(f"    {aid}: total delay = {delay_info['total_delay_min']} min "
                      f"across {n*2} legs")

    # ------------------------------------------------------------------
    # Bonus 2: ASCII route maps
    # ------------------------------------------------------------------
    if print_ascii:
        print("\n  [Bonus] ASCII Route Visualisation:")
        for aid in sorted(assignments):
            if assignments[aid]:          # only agents with packages
                route_map = ascii_route_map(aid, results[aid]["route"])
                print(route_map)

    # ------------------------------------------------------------------
    # Bonus 3: Export top performer to CSV
    # ------------------------------------------------------------------
    export_top_performer_csv(report, csv_path)

    print(f"\n{'='*55}\n")
    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Usage:
        python delivery_system.py [input.json] [report.json]

    Defaults:
        input  → data.json
        report → report.json
    """
    input_file  = sys.argv[1] if len(sys.argv) > 1 else "data.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "report.json"

    if not Path(input_file).exists():
        print(f"[✗] Input file not found: {input_file}")
        sys.exit(1)

    run(input_file, report_path=output_file)
