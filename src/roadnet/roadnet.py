from typing import Dict, List

from src.roadnet.drivable import Drivable
from src.roadnet.intersection import Intersection
from src.roadnet.lane import Lane
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road
from src.utility.utility import Point


class RoadNet:
    def __init__(self):
        self._roads: List[Road] = []
        self._intersections: List[Intersection] = []
        self._road_map: Dict[str, Road] = {}
        self._inter_map: Dict[str, Intersection] = {}
        self._drivable_map: Dict[str, Drivable] = {}
        self._lanes: List[Lane] = []
        self._lane_links: List[LaneLink] = []
        self._drivables: List[Drivable] = []

    def get_point(self, p1: Point, p2: Point, a: float):
        return Point((p2.x - p1.x) * a + p1.x, (p2.y - p1.y) * a + p1.y)

    def load_from_json(self, json_file_name):
        # TODO Implementation for loadFromJson
        pass

    def convert_to_json(self, allocator):
        # TODO Implementation for convertToJson
        pass

    def get_roads(self):
        return self._roads

    def get_intersections(self):
        return self._intersections

    def get_road_by_id(self, id):
        return self._road_map.get(id)

    def get_intersection_by_id(self, id):
        return self._inter_map.get(id)

    def get_drivable_by_id(self, id):
        return self._drivable_map.get(id)

    def get_lanes(self):
        return self._lanes

    def get_lane_links(self):
        return self._lane_links

    def get_drivables(self):
        return self._drivables

    def reset(self):
        for road in self._roads:
            road.reset()

        for intersection in self._intersections:
            intersection.reset()
