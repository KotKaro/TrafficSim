from typing import List

from src.roadnet.cross import Cross
from src.roadnet.drivable import Drivable, DrivableType
from src.roadnet.lane import Lane
from src.roadnet.road_link import RoadLink


class LaneLink(Drivable):
    def __init__(self):
        self.roadLink: RoadLink = None
        self.startLane: Lane = None
        self.endLane: Lane = None
        self.crosses: List[Cross] = []

        self.width = 4
        self.maxSpeed = 10000  # TODO
        self.drivableType = DrivableType.LANELINK  # Define DrivableType as an enumeration

    def get_road_link(self):
        return self.roadLink

    def get_road_link_type(self):
        return self.roadLink.type

    def get_crosses(self):
        return self.crosses

    def get_start_lane(self) -> Lane:
        return self.startLane

    def get_end_lane(self):
        return self.endLane

    def is_available(self):
        return self.roadLink.isAvailable()

    def is_turn(self):
        return self.roadLink.isTurn()

    def reset(self):
        self.vehicles.clear()

    def get_id(self):
        start_lane_id = self.startLane.getId() if self.startLane else ""
        end_lane_id = self.endLane.getId() if self.endLane else ""
        return start_lane_id + "_TO_" + end_lane_id
