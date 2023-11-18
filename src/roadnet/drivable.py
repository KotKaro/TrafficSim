from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from src.utility.utility import Point
from src.vehicle.vehicle import Vehicle


class DrivableType(Enum):
    LANE = 0
    LANELINK = 1


class Drivable(ABC):
    def __init__(self, length, width, max_speed, drivable_type):
        self.length = length
        self.width = width
        self.max_speed = max_speed
        self.vehicles: List[Vehicle] = []
        self.points = []
        self.drivable_type = DrivableType(drivable_type)

    def get_vehicles(self):
        return self.vehicles

    def get_length(self):
        return self.length

    def get_width(self):
        return self.width

    def get_max_speed(self):
        return self.max_speed

    def get_vehicle_count(self):
        return len(self.vehicles)

    def get_drivable_type(self):
        return self.drivable_type

    def is_lane(self) -> bool:
        return self.drivable_type == DrivableType.LANE

    def is_lane_link(self):
        return self.drivable_type == DrivableType.LANELINK

    def get_first_vehicle(self):
        return self.vehicles[0] if self.vehicles else None

    def get_last_vehicle(self):
        return self.vehicles[-1] if self.vehicles else None

    def push_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def pop_vehicle(self):
        if self.vehicles:
            self.vehicles.pop(0)

    @abstractmethod
    def get_id(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def get_point_by_distance(self, distance: float) -> Point:
        return Point.get_point_by_distance(self.points, distance)

    def get_direction_by_distance(self, dis: float) -> Point:
        remain = dis
        for i in range(1, len(self.points)):
            double_len = (self.points[i + 1] - self.points[i]).len()
            if remain < double_len:
                return (self.points[i + 1] - self.points[i]).unit()
            else:
                remain -= double_len
