from colorama import Fore, init
import math
from datetime import datetime

from loaders import generate_packages, load_trucks
from genetic_algorithm import genetic_algorithm, load_chromosome
from simulation import run_simulation

init(autoreset=True)

def print_banner():
    print(Fore.YELLOW + """
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║        WGUPS Routing Service         ║
    ║       Feat. Genetic Algorithm        ║
    ║                                      ║
    ╚══════════════════════════════════════╝""")


def quit_service():
    print(Fore.YELLOW + """
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║    Thank you for using WGUPS!        ║
    ║         Have a great day.            ║
    ║                                      ║
    ╚══════════════════════════════════════╝""")
    print()

def input_int():
    while True:
        choice = input('>>> ')
        try:
            choice = int(choice)
        except ValueError:
            print('Please enter a valid number.')
            continue
        return choice

def input_float():
    while True:
        choice = input('>>> ')
        try:
            choice = float(choice)
        except ValueError:
            print('Please enter a valid number.')
            continue
        return choice

def input_time():
    while True:
        time_str = input('>>> ').strip().lower()
        try:
            t = datetime.strptime(time_str, '%I:%M %p').time()
            return datetime.combine(datetime(2000, 1, 1), t)
        except ValueError:
            print('Please enter a valid time in the correct format.')

def find_delivery_status(package, truck, time):
    # at the hub yet?
    if package.delay_time and time < package.delay_time:
        return 'DELAYED'

    # is it at the hub waiting for a truck to leave?
    if time < truck.departure_time:
        return 'AT HUB'

    # is it late? (if package was not delivered by deadline or still on truck)
    if package.deadline and time > package.deadline:
        if package.delivery_time is None or package.delivery_time > package.deadline:
            return 'LATE'

    # has it been delivered yet?
    if package.delivery_time is None or package.delivery_time > time:
        return 'EN ROUTE'

    # else, it must be delivered
    return 'DELIVERED'

def get_truck_for_package(package, trucks):
    for t in trucks:
        if package in t.packages:
            return t
    print('Package not found')
    return None

def run_cli(num_addresses, address_to_id, id_to_address, distance_matrix):
    print_banner()
    packages = None
    while True:
        print()
        print('Would you like to:')
        print('[1] Run GA with custom specs?')
        print('[2] Package lookup/status? (must have already ran GA)')
        print('[3] Exit')

        choice = input_int()
        if choice == 1:
            packages, trucks, package_num = run_ga(num_addresses,
                                address_to_id, id_to_address, distance_matrix)

        elif choice == 2:
            if packages is None:
                print('You need to run the GA at least once to generate ' \
                    'package and truck objects.')
            else:
                run_lookup(packages, trucks, package_num)

        elif choice == 3:
            quit_service()
            return
        else:
            print('Please enter a valid number.')

def run_ga(num_addresses, address_to_id, id_to_address, distance_matrix):
    packages = None
    trucks = None
    print()
    print('How many packages would you like to generate?')
    package_num = input_int()

    print('What proportion of packages would you like to have deadlines?')
    print('(proportions must be a number between 0 and 1)')
    while True:
        deadline_num = input_float()
        if 0 <= deadline_num <= 1: break
        else: print('Please enter a valid number.')

    print('What proportion of packages would you like to be delayed?')
    while True:
        delay_num = input_float()
        if 0 <= delay_num <= 1: break
        else: print('Please enter a valid number.')

    print('What proportion of packages would you like to be refrigerated?')
    while True:
        refrig_num = input_float()
        if 0 <= refrig_num <= 1: break
        else: print('Please enter a valid number.')

    print('What would you like the capacity of a single truck to be?')
    print('(how many packages can it hold)')
    capacity = input_int()

    truck_num = math.ceil(float(package_num) / float(capacity))
    print(f'Minimum number of trucks required: {truck_num}')
    print(f'Enter {truck_num} to choose that as your truck number.')
    print('Otherwise, enter a higher number if you\'d like more trucks')
    while True:
        truck_num_input = input_int()
        if truck_num_input >= truck_num:
            truck_num = truck_num_input
            break
        else:
            print('Please enter a valid number.')

    refrig_truck_num = math.ceil(
        (float(package_num) * float(refrig_num)) / float(capacity))
    print(f'Minmimum number of refrigerated trucks required: '\
          f'{refrig_truck_num}')
    print(f'How many of your {truck_num} trucks would you like to be '\
          'refrigerated?')
    print(f'(recommended amount: {refrig_truck_num + 1})')
    while True:
        refrig_truck_num_input = input_int()
        if refrig_truck_num_input >= refrig_truck_num:
            refrig_truck_num = refrig_truck_num_input
            break
        else:
            print('Please enter a valid number.')

    print('What would you like the population size of the GA to be?')
    pop_size = input_int()

    print('How many generations would you like the GA to run for?')
    print('(must be a multiple of 10 so the GA can keep track of '\
          'generations accurately)')
    print('(tip: you can input a ridiculously large number (10000000) and ' \
        'the GA will automatically end once a certain amount of ' \
        'generations pass without an improved score)')
    while True:
        generations = input_int()
        if generations % 10 == 0: break
        else: print('Please enter a valid number.')

    print('What would you like the mutation rate of the GA to be?')
    while True:
        mutation_rate = input_float()
        if 0 <= mutation_rate <= 1: break
        else: print('Please enter a valid number.')

    print()

    print('Now running GENETIC ALGORITHM!')
    packages = generate_packages(package_num, deadline_num, delay_num,
                                 refrig_num, id_to_address, num_addresses)
    trucks = load_trucks(truck_num, refrig_truck_num, capacity)

    print()

    best_chromosome, bundles = genetic_algorithm(
        packages, truck_num, trucks, capacity, address_to_id, distance_matrix,
        mutation_rate, pop_size, generations)
    load_chromosome(best_chromosome, bundles, packages, trucks)

    # run final simulation with best chromosome
    trucks = run_simulation(trucks, address_to_id, distance_matrix, capacity)
    return packages, trucks, package_num

def run_lookup(packages, trucks, package_num):
    print()
    print('How would you like to find your package?')
    print('[1] By ID')
    print('[2] By address')
    while True:
        choice = input_int()
        if choice == 1 or choice == 2: break
        else: print('Please enter a valid number.')

    if choice == 1:
        print()
        print('Please enter package ID.')
        print(f'(package IDs are in the range 0 to {package_num - 1})')
        while True:
            package_id = input_int()
            if 0 <= package_id < package_num: break
            else: print('Please enter a valid number.')
        package = packages[package_id]
        truck = get_truck_for_package(package, trucks)

        print('Please enter time in \'HH:MM am/pm\' format.')
        t = input_time()

        status = find_delivery_status(package, truck, t)
        print_package_status(package, status, t)

    if choice == 2:
        while True:
            print()
            print('Please enter the address your package is assigned to.')
            print('In case you don\'t know any off hand, here are a few.')
            print()
            print('300 State St, Salt Lake City, UT 84103')
            print('3900 S Wasatch Blvd, Salt Lake City,UT 84124')
            print('1200 W 7800 S, West Jordan, UT 84088')
            print()
            print('Please copy and paste the exact address, or it may not work.')

            address = input('>>> ')
            packages_to_address = [p_id for p_id, p in packages.items()
                                   if p.address == address]

            if len(packages_to_address) == 0:
                print('Address not found among packages. Would you like to...')
                print('[1] Return home?')
                print('[2] Try again?')
                choice = input_int()
                while True:
                    if not (choice == 1 or choice == 2):
                        print('Please enter a valid number')
                    else:
                        break
                if choice == 1:
                    return
                if choice == 2:
                    continue

            print('Please enter time in \'HH:MM am/pm\' format.')
            t = input_time()

            print('Package(s) status with this address:')
            for package_id in packages_to_address:
                package = packages[package_id]
                # find truck package is on
                truck = get_truck_for_package(package, trucks)
                status = find_delivery_status(package, truck, t)
                print_package_status(package, status, t)
            break

def print_package_status(package, status, t):
    if t >= package.delivery_time:
        delivery_time = package.delivery_time
    else:
        delivery_time = 'N/A'
    if not package.delay_time:
        delay_time = 'N/A'
    else:
        delay_time = package.delay_time
    if not package.deadline:
        deadline = 'N/A'
    else:
        deadline = package.deadline
    print(f'Package {package.package_id} | Status: {status} | ' \
        f'Delivery Time: {delivery_time} | Delayed: {delay_time} | ' \
            f'Deadline: {deadline}')