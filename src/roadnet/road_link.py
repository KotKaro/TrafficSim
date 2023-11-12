from enum import Enum, auto
from typing import List

from src.roadnet.intersection import Intersection
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road


class RoadLinkType(Enum):
    go_straight = 3
    turn_left = 2
    turn_right = 1


class RoadLink:
    def __init__(self):
        self.intersection: Intersection = None
        self.startRoad: Road = None
        self.endRoad: Road = None
        self.type: RoadLinkType = None
        self.lane_links: List[LaneLink] = []
        self.index: int = None

    def get_lane_link_pointers(self):
        return self.lane_links

    def get_start_road(self):
        return self.startRoad

    def get_end_road(self):
        return self.endRoad

    def is_available(self):
        return self.intersection.traffic_light.get_current_phase().road_link_available[self.index]

    def is_turn(self):
        return self.type == RoadLinkType.turn_left or self.type == RoadLinkType.turn_right

    def reset(self):
        for laneLink in self.lane_links:
            laneLink.reset()
