from loaders import load_csvs
from cli import run_cli

if __name__ == "__main__":
    # load address dictionaries the distance matrix from csv files
    num_addresses, address_to_id, id_to_address, distance_matrix = \
        load_csvs()

    run_cli(num_addresses, address_to_id, id_to_address, distance_matrix)