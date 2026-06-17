from datetime import timedelta

def run_simulation(trucks, address_to_id, distance_matrix, capacity):
    deadline_violations = 0
    refrig_violations = 0
    capacity_violations = 0
    total_fleet_mileage = 0

    for truck in trucks:
        truck.mileage = 0
        print()
        print(f'Truck {truck.truck_id}:')
        for package in truck.packages:
            if package.delay_time is not None:
                if package.delay_time > truck.departure_time:
                    truck.departure_time = package.delay_time

        print(f'Departure_time: {truck.departure_time}')
        print(f'Capacity: {len(truck.packages)} / {capacity}')

        current_location = truck.current_location
        current_time = truck.departure_time

        for package in truck.packages:
            location_index = address_to_id[current_location]
            address_index = address_to_id[package.address]

            distance = distance_matrix[location_index][address_index]
            travel_time = distance / 18.0
            current_time += timedelta(hours=travel_time)
            truck.mileage += distance

            current_location = package.address
            package.delivery_time = current_time

            if package.deadline and package.delivery_time > package.deadline:
                deadline_violations += 1
            if package.refrigerated and not truck.refrigerated_capable:
                refrig_violations += 1

        location_index = address_to_id[current_location]
        distance = distance_matrix[location_index][0]
        travel_time = distance / 18.0
        current_time += timedelta(hours=travel_time)
        truck.mileage += distance
        print(f'Truck mileage: {truck.mileage:.2f}, return time: {current_time}')
        total_fleet_mileage += truck.mileage

        if len(truck.packages) > capacity:
            capacity_violations += (len(truck.packages) - capacity)

    print()
    print(f'---RESULTS---')
    print(f'Total Fleet Mileage: {total_fleet_mileage:.2f}')
    print(f'Total Deadline Violations: {deadline_violations}')
    print(f'Total Refrigeration Violations: {refrig_violations}')
    print(f'Total Capacity Violations: {capacity_violations}')

    return trucks