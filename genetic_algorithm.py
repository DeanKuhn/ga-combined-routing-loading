import random
from datetime import timedelta, datetime

def bundle_packages(packages):
    # group by address first
    address_groups = {}
    for p_id, p in packages.items():
        if p.address not in address_groups:
            address_groups[p.address] = []
        address_groups[p.address].append(p)

    bundles = {}
    bundle_id_counter = 0

    for address, p_list in address_groups.items():
        # sort packages by deadline to find tightest constraint
        p_list.sort(key=lambda x: x.deadline if x.deadline else datetime.max)

        current_bundle_packages = []

        for p in p_list:
            if not current_bundle_packages:
                current_bundle_packages.append(p)
                continue

            # find constraints of the current potential bundle
            max_delay = max((pkg.delay_time for pkg in current_bundle_packages
                             if pkg.delay_time), default=None)
            min_deadline = min((pkg.deadline for pkg in current_bundle_packages
                                if pkg.deadline), default=datetime.max)

            # check if adding package makes the bundle impossible
            new_delay = p.delay_time if p.delay_time else datetime.min
            new_deadline = p.deadline if p.deadline else datetime.max

            # add in drive time buffer
            buffer = timedelta(minutes=45)
            is_compatible = True
            if max_delay and new_deadline < max_delay:
                is_compatible = False
            if new_delay + buffer > min_deadline:
                is_compatible = False

            if is_compatible:
                current_bundle_packages.append(p)
            else:
                bundles[bundle_id_counter] = \
                    finalize_bundle(current_bundle_packages)
                bundle_id_counter += 1
                current_bundle_packages = [p]

        if current_bundle_packages:
            bundles[bundle_id_counter] = \
                finalize_bundle(current_bundle_packages)
            bundle_id_counter += 1

    return bundles

def finalize_bundle(p_list):
    return {
        'package_ids': [p.package_id for p in p_list],
        'address': p_list[0].address,
        'deadline': min((p.deadline for p in p_list if p.deadline), default=None),
        'delay_time': max((p.delay_time for p in p_list if p.delay_time), default=None),
        'refrigerated': any(p.refrigerated for p in p_list),
        'total_weight': sum(p.weight for p in p_list)
    }

def create_population(bundles, num_trucks, pop_size):
    population = []
    bundle_ids = list(bundles.keys())

    for _ in range(pop_size):
        random.shuffle(bundle_ids)
        chromosome = []

        # this evenly places sentinels to give the GA a better starting chance
        average_load = len(bundle_ids) // num_trucks
        for i in range(num_trucks):
            start = i * average_load
            # else handles any remainders in the division
            end = (i + 1) * average_load if i < num_trucks - 1 \
                else len(bundle_ids)
            chromosome.extend(bundle_ids[start:end])
            # add sentinel if not last truck
            if i < num_trucks - 1:
                chromosome.append(-(i + 1))
        population.append(chromosome)
    return population

def fitness(chromosome, trucks, capacity, bundles, address_to_id,
            distance_matrix):
    distance_score = 0
    total_minutes_late = 0
    num_late_packages = 0
    num_capacity_over = 0
    refrig_violations = 0

    # first, find different routes
    routes = []
    current_route = []
    for gene in chromosome:
        if (gene < 0):
            routes.append(current_route)
            current_route = []
        else:
            current_route.append(gene)
    routes.append(current_route)

    for i, route in enumerate(routes):
        if i >= len(trucks): break
        curr_truck = trucks[i]

        route_load = 0
        departure_time = curr_truck.departure_time

        # find route load
        for bundle_id in route:
            bundle = bundles[bundle_id]
            route_load += len(bundle['package_ids'])
            # find departure time for truck
            if bundle['delay_time'] and bundle['delay_time'] > departure_time:
                departure_time = bundle['delay_time']

        # score capacity
        if route_load > capacity:
            num_capacity_over += (route_load - capacity)

        # assign time and location
        current_time = departure_time
        current_location = curr_truck.current_location

        # simulated route execution
        for bundle_id in route:
            bundle = bundles[bundle_id]
            location_index = address_to_id[current_location]
            address_index = address_to_id[bundle['address']]

            distance = distance_matrix[location_index][address_index]
            # distance score
            distance_score += distance

            travel_time = distance / 18.0
            current_time += timedelta(hours=travel_time)

            if bundle['deadline'] and current_time > bundle['deadline']:
                    num_late_packages += len(bundle['package_ids'])

                    lateness = current_time - bundle['deadline']
                    minutes_late = lateness.total_seconds() / 60
                    total_minutes_late += minutes_late

            if bundle['refrigerated'] and not curr_truck.refrigerated_capable:
                refrig_violations += len(bundle['package_ids'])

            current_location = bundle['address']

        # return to the HUB, score based on how far
        distance_score += distance_matrix[address_to_id[current_location]][0]

    # scoring constraints, easy to fine-tune
    score = (distance_score +
             (total_minutes_late * 10) +
             (num_late_packages * 200) +
             (num_capacity_over * 2000) +
             (refrig_violations * 2000))

    return score

def get_population_fitness(population, trucks, capacity, bundles,
                           address_to_id, distance_matrix):
    scored_population = []
    for chromosome in population:
        score = fitness(chromosome, trucks, capacity, bundles,
                        address_to_id, distance_matrix)
        scored_population.append((score, chromosome))
    return scored_population

def tournament_selection(scored_population):
    k = 3
    selection = random.sample(scored_population, k)
    selection.sort(key=lambda x: x[0])
    winner = selection[0][1]
    return winner.copy()

def ordered_crossover(parent1, parent2):
    size = len(parent1)
    child = [None] * size

    # lock sentinel positions for parent 1
    for i, gene in enumerate(parent1):
        if gene < 0:
            child[i] = gene

    # find package orders for parent 2
    p2_packages = [gene for gene in parent2 if not (gene < 0)]

    # fill in the gaps
    p2_index = 0
    for i in range(size):
        if child[i] is None:
            child[i] = p2_packages[p2_index]
            p2_index += 1

    return child

def mutate(chromosome, mutation_rate, stagnation_counter):
    # standard swap, do this often
    if random.random() < (mutation_rate * 2):
        package_indices = \
            [i for i, g in enumerate(chromosome) if not (g < 0)]
        i, j = random.sample(package_indices, 2)
        chromosome[i], chromosome[j] = chromosome[j], chromosome[i]

    # scramble mutation, only if 'stuck'
    scramble_chance = 0.01 + (stagnation_counter * 0.001)
    if random.random() < scramble_chance:
        package_indices = \
            [i for i, g in enumerate(chromosome) if not (g < 0)]
        window_size = random.randint(3, 8)
        start_position = random.randint(0, len(package_indices) - window_size)

        # select target indices and the actual genes
        target_indices = \
            package_indices[start_position:start_position + window_size]
        genes_to_scramble = [chromosome[i] for i in target_indices]
        random.shuffle(genes_to_scramble)

        for i, original_index in enumerate(target_indices):
            chromosome[original_index] = genes_to_scramble[i]

    # inversion mutation
    if random.random() < mutation_rate:
        package_indices = \
            [i for i, g in enumerate(chromosome) if not (g < 0)]
        if len(package_indices) < 2: return

        index1, index2 = sorted(random.sample(range(len(package_indices)), 2))
        target_indices = package_indices[index1:index2 + 1]
        reversed_values = [chromosome[i] for i in target_indices][::-1]
        for i, original_index in enumerate(target_indices):
            chromosome[original_index] = reversed_values[i]

    # sentinel shift, not often
    if random.random() < (mutation_rate / 2):
        sentinel_indices = \
            [i for i, g in enumerate(chromosome) if (g < 0)]
        index = random.choice(sentinel_indices)

        shift = random.choice([-1, 1])
        new_index = index + shift

        if 0 <= new_index < len(chromosome) \
            and not (chromosome[new_index] < 0):

            chromosome[index], chromosome[new_index] = \
                chromosome[new_index], chromosome[index]

def genetic_algorithm(packages, num_trucks, trucks, capacity,
        address_to_id, distance_matrix, mutation_rate, pop_size, generations):

    # transform packages to bundles
    bundles = bundle_packages(packages)

    # define original mutation rate
    original_mutation_rate = mutation_rate

    # create initial population
    population = create_population(bundles, num_trucks, pop_size)
    previous_best_score = float('inf')
    stagnation_counter = 0
    milestone_count = 0

    for generation in range(generations):
        # get the overall population fitness for each chromosome
        scored_pop = get_population_fitness(population, trucks, capacity,
                                    bundles, address_to_id, distance_matrix)

        # sort by the highest scorers
        scored_pop.sort(key=lambda x: x[0])
        best_score = scored_pop[0][0]
        early_chromosome = scored_pop[0][1]

        # implement adaptive mutation rates
        # require >0.1% improvement to reset stagnation — prevents thrashing
        # in flat fitness landscapes where tiny gains would keep the counter low
        if previous_best_score == float('inf') or \
                best_score < previous_best_score * 0.999:
            previous_best_score = best_score
            stagnation_counter = 0
            mutation_rate = original_mutation_rate
        else:
            stagnation_counter += 1

        if stagnation_counter > 50:
            mutation_rate = min(0.25, mutation_rate * 2)

        # early return
        if stagnation_counter > 500:
            print(f'Early return | Gen {generation} | ' \
                  f'Best Score = {best_score:.2f}')
            return early_chromosome, bundles

        # progress update
        ten_percent_num = generations / 10
        if generation % ten_percent_num == 0:
            milestone_count += 1
            print(
            f'{milestone_count} / 10 | Gen {generation} | Best Score = {best_score:.2f}')

        # start creating new population
        new_population = []
        # append the best scorer
        for i in range(5):
            new_population.append(scored_pop[i][1].copy())

        # run two tournaments, each parent being the winner
        while len(new_population) < pop_size:
            p1 = tournament_selection(scored_pop)
            p2 = tournament_selection(scored_pop)

            # potentially create a child from these parents
            if random.random() < 0.8:
                child = ordered_crossover(p1, p2)
            else:
                child = p1.copy()
            # potentially mutate the child
            mutate(child, mutation_rate, stagnation_counter)
            # add to the new population
            new_population.append(child)
        population = new_population

    # get the score of the final population
    scored_pop = get_population_fitness(population, trucks, capacity, bundles,
                                        address_to_id, distance_matrix)

    # sort and find the best chromosome
    scored_pop.sort(key=lambda x: x[0])
    print(f'10 / 10 | Final Gen | Best Score = {scored_pop[0][0]:.2f}')
    best_chromosome = scored_pop[0][1]

    return best_chromosome, bundles

# creates package arrays for each truck
def load_chromosome(best_chromosome, bundles, packages, trucks):
    routes = []
    current_route = []
    for gene in best_chromosome:
        if (gene < 0):
            routes.append(current_route)
            current_route = []
        else:
            current_route.append(gene)
    routes.append(current_route)

    for i, route in enumerate(routes):
        if i >= len(trucks): break
        truck = trucks[i]
        truck.packages = []
        for bundle_id in route:
            bundle = bundles[bundle_id]
            for package_id in bundle['package_ids']:
                truck.packages.append(packages[package_id])