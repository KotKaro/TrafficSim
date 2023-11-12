from enum import Enum, auto


class RoadLinkType(Enum):
    go_straight = 3
    turn_left = 2
    turn_right = 1


class RoadLink:
    def __init__(self):
        self.intersection = None
        self.startRoad = None
        self.endRoad = None
        self.type = None
        self.laneLinks = []
        self.laneLinkPointers = []
        self.index = None

    def get_lane_links(self):
        return self.laneLinks

    def get_lane_link_pointers(self):
        if len(self.laneLinkPointers) > 0:
            return self.laneLinkPointers

        for laneLink in self.laneLinks:
            self.laneLinkPointers.append(laneLink)

        return self.laneLinkPointers

    def get_start_road(self):
        return self.startRoad

    def get_end_road(self):
        return self.endRoad

    def is_available(self):
        return self.intersection.trafficLight.getCurrentPhase().roadLinkAvailable[self.index]

    def is_turn(self):
        return self.type == RoadLinkType.turn_left or self.type == RoadLinkType.turn_right

    def reset(self):
        for laneLink in self.laneLinks:
            laneLink.reset()
