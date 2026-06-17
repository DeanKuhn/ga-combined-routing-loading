import csv
from datetime import datetime, timedelta
import random

from package import Package
from truck import Truck

def generate_packages(num_packages, chance_deadline, chance_delay,
                      chance_refrigerated, id_to_address, num_addresses):

    deadlines = [datetime(2000, 1, 1, 9, 0), datetime(2000, 1, 1, 10, 00),
                 datetime(2000, 1, 1, 11, 00), datetime(2000, 1, 1, 12, 0)]

    delays = [datetime(2000, 1, 1, 8, 30), datetime(2000, 1, 1, 9, 30)]

    notes = ['Fragile - handle with care', 'Signature required']
    chance_note = 0.5

    packages = {}

    for i in range(num_packages):
        # choose a random address from the dictionary
        n = random.randint(1, (num_addresses-1))

        # independent rolls for every constraint
        deadline = random.choice(deadlines) \
            if random.random() < chance_deadline else None
        delay = random.choice(delays) \
            if random.random() < chance_delay else None
        refrigerated = True if random.random() < chance_refrigerated else None
        note = random.choice(notes) if random.random() < chance_note else None

        if deadline and delay:
            if deadline < delay + timedelta(hours=1):
                deadline = delay + timedelta(hours=2)

        package = Package(
            package_id=i,
            address=id_to_address[n],
            deadline=deadline,
            weight=random.randint(5, 100),
            notes=note,
            refrigerated=refrigerated,
            delivery_time=None,
            delay_time=delay
        )
        packages[i] = package

    return packages

def load_csvs():
    num_addresses = 0
    # create two dictionaries, one mapping address to location ID, and one
    # mapping location ID to address
    with open('data/locations.csv', 'r') as locations:
        csv_reader = csv.DictReader(locations, delimiter=',')
        address_to_id = {}
        id_to_address = {}
        for row in csv_reader:
            # include city, state, and zip in case of duplicate addresses
            # in different cities
            address = \
                f'{row['Address']}, {row['City']}, {row['State']} {row['Zip']}'

            address_to_id[address] = int(row['Location ID'])
            id_to_address[int(row['Location ID'])] = address
            num_addresses += 1

    # create distance matrix
    with open('data/distances.csv', 'r') as distances:
        csv_reader = csv.reader(distances, delimiter=',')
        distance_matrix =\
        [[None for _ in range(num_addresses)] for _ in range(num_addresses)]

        row_num = 0
        for row in csv_reader:
            col_num = 0
            for distance in row:
                distance_matrix[row_num][col_num] = float(distance)
                col_num += 1
            row_num += 1

    return num_addresses, address_to_id, id_to_address, distance_matrix

def load_trucks(num_trucks, num_refrig, num_capacity):
    # create trucks based on the number of trucks,
    # refrigerated trucks, and capacity
    trucks = []
    for i in range(num_trucks):
        truck_id = i + 1
        # make the first trucks the refrig trucks
        refrig = (i < num_refrig)

        truck = Truck(
            truck_id=truck_id,
            current_location='4001 South 700 East, Salt Lake City, UT 84107',
            mileage=0.0,
            departure_time=datetime(2000, 1, 1, 8, 0),
            refrigerated_capable=refrig,
            capacity=num_capacity
            )
        trucks.append(truck)

    return trucks