import json
import os
from datetime import datetime, timezone

def _stop_status(stop_packages):
    deadlines = [p.deadline for p in stop_packages if p.deadline]
    if not deadlines:
        return 'N/A'
    if any(p.deadline and p.delivery_time and p.delivery_time > p.deadline
           for p in stop_packages):
        return 'LATE'
    return 'ON TIME'

def _finalize_stop(stop_packages):
    arrival_time = stop_packages[0].delivery_time
    return {
        'package_ids': [p.package_id for p in stop_packages],
        'address': stop_packages[0].address,
        'arrival_time': arrival_time.isoformat() if arrival_time else None,
        'status': _stop_status(stop_packages),
    }

def build_routes(trucks):
    # group consecutive same-address packages into stops — load_chromosome()
    # appends packages bundle-by-bundle, so same-address packages from the
    # same bundle are already adjacent in truck.packages
    routes = []
    for truck in trucks:
        stops = []
        current_stop = []
        for package in truck.packages:
            if current_stop and package.address == current_stop[-1].address:
                current_stop.append(package)
            else:
                if current_stop:
                    stops.append(_finalize_stop(current_stop))
                current_stop = [package]
        if current_stop:
            stops.append(_finalize_stop(current_stop))
        routes.append({'truck_id': truck.truck_id, 'stops': stops})
    return routes

def export_results(trucks, parameters, final_score, convergence_history,
                    output_path):
    results = {
        'run_timestamp': datetime.now(timezone.utc).isoformat(),
        'parameters': parameters,
        'final_score': final_score,
        'convergence': convergence_history,
        'routes': build_routes(trucks),
    }

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    return results
