from collections import deque
from typing import List

from src.roadnet.drivable import Drivable
from src.roadnet.road import Road
from src.roadnet.segment import Segment


class Lane(Drivable):
    history_len = 240

    def __init__(self, width: float = 0, max_speed: float = 0, lane_index: int = -1, belong_road: Road = None):
        self.width: float = width
        self.max_speed: float = max_speed
        self.lane_index = lane_index
        self.segments: List[Segment] = []
        self.lane_links: List[LaneLink] = []
        self.belong_road: Road = belong_road
        self.waiting_buffer = deque()
        self.history = []
        self.drivable_type = Drivable.LANE

        self.historyVehicleNum = 0
        self.historyAverageSpeed = 0

    def get_id(self):
        return self.belong_road.get_id() + '_' + str(self.getLaneIndex())

    def available(self, vehicle):
        # TODO Implement the available method logic here
        pass

    def can_enter(self, vehicle):
        # TODO Implement the canEnter method logic here
        pass

    def get_inner_lane(self):
        if self.lane_index > 0:
            return self.belong_road.lanes[self.lane_index - 1]
        else:
            return None

    def get_outer_lane(self):
        lane_num = len(self.belong_road.lanes)
        if self.lane_index < lane_num - 1:
            return self.belong_road.lanes[self.lane_index + 1]
        else:
            return None

    def getStartIntersection(self):
        return self.belong_road.startIntersection

    def getEndIntersection(self):
        return self.belong_road.endIntersection

    def getLaneLinksToRoad(self, road):
        # TODO Implement the getLaneLinksToRoad method logic here
        pass

    def reset(self):
        # TODO Implement the reset method logic here
        pass

    def getWaitingBuffer(self):
        return self.waiting_buffer

    def pushWaitingVehicle(self, vehicle):
        self.waiting_buffer.append(vehicle)

    def buildSegmentation(self, numSegs):
        # TODO Implement the buildSegmentation method logic here
        pass

    def initSegments(self):
        # TODO Implement the initSegments method logic here
        pass

    def getSegment(self, index):
        return self.segments[index]

    def getSegments(self):
        return self.segments

    def getSegmentNum(self):
        return len(self.segments)

    def getVehiclesBeforeDistance(self, dis, segmentIndex, deltaDis=50):
        # TODO Implement the getVehiclesBeforeDistance method logic here
        pass

    def updateHistory(self):
        # TODO Implement the updateHistory method logic here
        pass

    def getVehicleBeforeDistance(self, dis, segmentIndex):
        # TODO Implement the getVehicleBeforeDistance method logic here
        pass

    def getVehicleAfterDistance(self, dis, segmentIndex):
        # TODO Implement the getVehicleAfterDistance method logic here
        pass
