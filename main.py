import argparse

from loaders import load_csvs
from cli import run_cli, run_non_interactive

def parse_args():
    parser = argparse.ArgumentParser(
        description='WGUPS Routing Service — GA-based VRP-TW solver')
    parser.add_argument('--packages', type=int,
        help='Number of packages to generate. Supplying this flag switches '
             'to non-interactive mode.')
    parser.add_argument('--trucks', type=int, default=None,
        help='Number of trucks (default: minimum required for capacity)')
    parser.add_argument('--capacity', type=int, default=16,
        help='Per-truck package capacity (default: 16)')
    parser.add_argument('--deadline-pct', type=float, default=0.3,
        help='Proportion of packages with a deadline (default: 0.3)')
    parser.add_argument('--delay-pct', type=float, default=0.1,
        help='Proportion of packages with a delay (default: 0.1)')
    parser.add_argument('--refrig-pct', type=float, default=0.1,
        help='Proportion of packages requiring refrigeration (default: 0.1)')
    parser.add_argument('--pop-size', type=int, default=150,
        help='GA population size (default: 150)')
    parser.add_argument('--generations', type=int, default=500,
        help='Maximum GA generations (default: 500)')
    parser.add_argument('--mutation-rate', type=float, default=0.05,
        help='Base GA mutation rate (default: 0.05)')
    parser.add_argument('--seed', type=int, default=None,
        help='Random seed for reproducible runs')
    parser.add_argument('--output', type=str, default='data/ga_results.json',
        help='Output path for the results JSON (default: data/ga_results.json)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # load address dictionaries the distance matrix from csv files
    num_addresses, address_to_id, id_to_address, distance_matrix = \
        load_csvs()

    if args.packages is not None:
        run_non_interactive(args, num_addresses, address_to_id,
                            id_to_address, distance_matrix)
    else:
        run_cli(num_addresses, address_to_id, id_to_address, distance_matrix)
