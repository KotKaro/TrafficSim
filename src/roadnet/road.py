from typing import List

from src.roadnet.lane import Lane
from src.roadnet.traffic_light import Intersection
from src.utility.utility import Point


class Road:
    def __init__(self, id, start_intersection: Intersection=None, end_intersection: Intersection=None, lanes:List[Lane]=None, points: List[Point]=None):
        self.id = id
        self.start_intersection = start_intersection
        self.end_intersection = end_intersection
        self.lanes = lanes if lanes is not None else []
        self.points = points if points is not None else []
        self.lane_pointers = []
        self.plan_route_buffer = []

    def get_id(self):
        return self.id

    def get_start_intersection(self):
        return self.start_intersection

    def get_end_intersection(self):
        return self.end_intersection

    def get_lanes(self):
        return self.lanes

    def get_lane_pointers(self):
        # TODO finish it
        # ... implementation based on C++ code ...

    def build_segmentation_by_interval(self, interval):
        # TODO finish it

        # ... implementation based on C++ code ...

    def connected_to_road(self, road):
        # TODO finish it

        # ... implementation based on C++ code ...

    def reset(self):
        # TODO finish it

        # ... implementation based on C++ code ...

    def get_width(self):
        # TODO finish it

        # ... implementation based on C++ code ...

    def get_length(self):
        # TODO finish it

        # ... implementation based on C++ code ...

    def average_length(self):
        # TODO finish it

        # ... implementation based on C++ code ...

    def get_average_speed(self):
        # TODO finish it

        # ... implementation based on C++ code ...

    def get_average_duration(self):
        # TODO finish it

        # ... implementation based on C++ code ...

    def get_plan_route_buffer(self):
        return self.plan_route_buffer

    def add_plan_route_vehicle(self, vehicle):
        self.plan_route_buffer.append(vehicle)

    def clear_plan_route_buffer(self):
        self.plan_route_buffer.clear()
