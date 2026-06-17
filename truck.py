from datetime import datetime

class Truck:
    def __init__(
            self,
            truck_id,
            current_location,
            mileage,
            departure_time,
            refrigerated_capable,
            capacity
            ):
        self.truck_id = truck_id
        self._packages = []
        self._current_location = current_location
        self._mileage = mileage
        self._departure_time = departure_time
        self._refrigerated_capable = refrigerated_capable
        self._capacity = capacity

    @property
    def truck_id(self):
        return self._truck_id

    @truck_id.setter
    def truck_id(self, value):
        self._truck_id = value

    @property
    def packages(self):
        return self._packages

    @packages.setter
    def packages(self, value):
        self._packages = value

    @property
    def current_location(self):
        return self._current_location

    @current_location.setter
    def current_location(self, value):
        self._current_location = value

    @property
    def mileage(self):
        return self._mileage

    @mileage.setter
    def mileage(self, value):
        self._mileage = value

    @property
    def departure_time(self):
        return self._departure_time

    @departure_time.setter
    def departure_time(self, value):
        if value is None or isinstance(value, datetime):
            self._departure_time = value
        else:
            raise ValueError("Time does not match datetime format.")

    @property
    def refrigerated_capable(self):
        return self._refrigerated_capable

    @refrigerated_capable.setter
    def refrigerated_capable(self, value):
        self._refrigerated_capable = value

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, value):
        self._capacity = value

    def __str__(self):
        details = [
            f"Package ID: {self._truck_id}",
            f"Departure Time: {self._departure_time}",
            f"Packages: {self._packages}",
            f"Refrig: {self._refrigerated_capable}"
            ]
        return "\n".join(details)