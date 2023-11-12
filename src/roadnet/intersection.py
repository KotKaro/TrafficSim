from typing import List

from src.roadnet.cross import Cross
from src.roadnet.road import Road
from src.roadnet.road_link import RoadLink
from src.roadnet.traffic_light import TrafficLight
from src.utility.utility import Point


class Intersection:
    def __init__(self, id, is_virtual, width, point: Point, traffic_light: TrafficLight, roads: List[Road], road_links: List[RoadLink], crosses: List[Cross], lane_links: List[LaneLink]):
        self.id = id
        self.is_virtual = is_virtual
        self.width = width
        self.point = point
        self.traffic_light = traffic_light
        self.roads = roads
        self.road_links = road_links
        self.crosses = crosses
        self.lane_links = lane_links

    def get_id(self):
        return self.id

    def get_traffic_light(self):
        return self.traffic_light

    def get_roads(self):
        return self.roads

    def get_road_links(self):
        return self.road_links

    def get_crosses(self):
        return self.crosses

    def is_virtual_intersection(self):
        return self.is_virtual

    def get_lane_links(self):
        if len(self.lane_links) > 0:
            return self.lane_links

        for road_link in self.road_links:
            road_lane_links = road_link.get_lane_links()
            self.lane_links.extend(road_lane_links)

        return self.lane_links

    def reset(self) -> None:
        self.traffic_light.reset()
        for roadLink in self.road_links:
            roadLink.reset()
        for cross in self.crosses:
            cross.reset()

    def get_outline(self):
        # TODO finish it

    def is_implicit_intersection(self):
        # TODO finish it
        # ... implementation based on C++ code ...

   def init_crosses(self):
        # TODO finish it
        # ... implementation based on C++ code ...