import math
from typing import List

from src.roadnet.lane import Lane
from src.roadnet.traffic_light import Intersection
from src.utility.utility import Point
from src.vehicle.vehicle import Vehicle


class Road:
    def __init__(self, id: str, start_intersection: Intersection = None, end_intersection: Intersection = None,
                 lanes: List[Lane] = None, points: List[Point] = None):
        self.id: str = id
        self.start_intersection: Intersection = start_intersection
        self.end_intersection: Intersection = end_intersection
        self.lanes: List[Lane] = lanes if lanes is not None else []
        self.points: List[Point] = points if points is not None else []
        self.lane_pointers = []
        self.plan_route_buffer: List[Vehicle] = []

    def get_id(self) -> str:
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
        number_of_segments = max(math.ceil(Point.get_length_of_points(self.points) / interval), 1)
        for lane in self.lanes:
            lane.build_segmentation(number_of_segments)

    def connected_to_road(self, road) -> bool:
        return any([len(lane.get_lane_links_to_road(road)) for lane in self.get_lanes()])

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
        vehicleNum = 0
        speedSum = 0
        for lane in self.lanes:
            vehicleNum += lane.historyVehicleNum
            speedSum += lane.historyAverageSpeed * lane.historyVehicleNum

        return speedSum / vehicleNum if vehicleNum else -1

    def get_average_duration(self):
        averageSpeed = self.get_average_speed()
        if averageSpeed < 0:
            return -1
        return self.average_length() / averageSpeed

    def get_plan_route_buffer(self) -> List[Vehicle]:
        return self.plan_route_buffer

    def add_plan_route_vehicle(self, vehicle):
        self.plan_route_buffer.append(vehicle)

    def clear_plan_route_buffer(self):
        self.plan_route_buffer.clear()

    def init_lanes_points(self) -> None:
        dsum = 0.0
        roadPoints = self.points

        assert(len(roadPoints) >= 2)

        if self.start_intersection.is_virtual_intersection() is False:
            width = self.start_intersection.width
            p1 = roadPoints[0]
            p2 = roadPoints[1]
            roadPoints[0] = p1 + (p2 - p1).unit() * width

        if self.end_intersection.is_virtual_intersection() is False:
            width = self.end_intersection.width
            p1 = roadPoints[len(roadPoints) - 2]
            p2 = roadPoints[len(roadPoints) - 1]
            roadPoints[len(roadPoints) - 1] = p2 - (p2 - p1).unit() * width

        for lane in self.lanes:
            dmin = dsum
            dmax = dsum + lane.width
            self.points.clear()

            for j in range(len(roadPoints)):
                lanePoints = lane.points
                if j == 0:
                    u = (roadPoints[1] - roadPoints[0]).unit()
                    v = -u.normal()
                    startPoint = roadPoints[j] + v * ((dmin + dmax) / 2.0)
                    lanePoints.push_back(startPoint)
                elif j + 1 == len(roadPoints):
                    u = (roadPoints[j] - roadPoints[j - 1]).unit()
                    v = -u.normal()
                    endPoint = roadPoints[j] + v * ((dmin + dmax) / 2.0)
                    lanePoints.push_back(endPoint)
                else:
                    u1 = (roadPoints[j + 1] - roadPoints[j]).unit()
                    u2 = (roadPoints[j] - roadPoints[j - 1]).unit()
                    u = (u1 + u2).unit()
                    v = -u.normal()
                    interPoint = roadPoints[j] + v * ((dmin + dmax) / 2.0)
                    lanePoints.push_back(interPoint)
            lane.length = Point.get_length_of_points(lane.points)
            dsum += lane.width

