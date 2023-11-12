import math
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

    def get_start_intersection(self) -> Intersection:
        return self.start_intersection

    def get_end_intersection(self):
        return self.end_intersection

    def get_lanes(self):
        return self.lanes

    def get_lane_pointers(self) -> List[Lane]:
        if len(self.lane_pointers) > 0:
            return self.lane_pointers

        for lane in self.lanes:
            self.lane_pointers.append(lane)

        return self.lane_pointers

    def build_segmentation_by_interval(self, interval) -> None:
        number_of_segments = max(math.ceil(self.get_length_of_points(self.points) / interval), 1)
        for lane in self.lanes:
            lane.buildSegmentation(number_of_segments)

    def connected_to_road(self, road) -> bool:
        return any([len(lane.getLaneLinksToRoad(road)) for lane in self.get_lanes()])

        for lane in self.get_lanes():
            if len(lane.getLaneLinksToRoad(road)) > 0:
                return True

        return False

    def reset(self):
        for lane in self.lanes:
            lane.reset()

    def get_width(self) -> float:
        return sum([lane.get_width() for lane in self.get_lanes()])

    def get_length(self):
        return sum([lane.get_length() for lane in self.get_lanes()])

    def average_length(self):
        return self.get_length() / len(self.get_lanes())

    def get_average_speed(self):
        vehicleNum = 0;
        speedSum = 0;
        for lane in self.lanes:
            vehicleNum += lane.historyVehicleNum
            speedSum += lane.historyAverageSpeed * lane.historyVehicleNum

        return speedSum / vehicleNum if vehicleNum else -1

    def get_average_duration(self):
        averageSpeed = self.get_average_speed()
        if averageSpeed < 0:
            return -1
        return self.average_length() / averageSpeed

    def get_plan_route_buffer(self):
        return self.plan_route_buffer

    def add_plan_route_vehicle(self, vehicle):
        self.plan_route_buffer.append(vehicle)

    def clear_plan_route_buffer(self):
        self.plan_route_buffer.clear()
