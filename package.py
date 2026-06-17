from datetime import datetime

class Package:
    def __init__(
                self,
                package_id,
                address,
                deadline,
                weight,
                notes,
                refrigerated,
                delivery_time = None,
                delay_time = None
                ):
        self._package_id = package_id
        self._address = address
        self._deadline = deadline
        self._weight = weight
        self._notes = notes
        self._refrigerated = refrigerated
        self._delivery_time = delivery_time
        self._delay_time = delay_time

    @property
    def package_id(self):
        return self._package_id

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def deadline(self):
        return self._deadline

    @deadline.setter
    def deadline(self, value):
        self._deadline = value

    @property
    def weight(self):
        return self._weight

    @property
    def notes(self):
        return self._notes

    @notes.setter
    def notes(self, value):
        self._notes = value

    @property
    def refrigerated(self):
        return self._refrigerated

    @refrigerated.setter
    def refrigerated(self, value):
        self._refrigerated = value

    @property
    def delivery_time(self):
        return self._delivery_time

    @delivery_time.setter
    def delivery_time(self, value):
        if value is None or isinstance(value, datetime):
            self._delivery_time = value
        else:
            raise ValueError("Time does not match datetime format.")

    @property
    def delay_time(self):
        return self._delay_time

    @delay_time.setter
    def delay_time(self, value):
        if value is None or isinstance(value, datetime):
            self._delay_time = value
        else:
            raise ValueError("Time does not match datetime format.")

    def __str__(self):
        details = [
            f"Package ID: {self._package_id}",
            f"Address: {self._address}",
            f"Deadline: {self._deadline}",
            f"Delivery Time: {self._delivery_time}"
            ]
        return "\n".join(details)