from src.roadnet.lane_link import LaneLink


class Cross:
    def __init__(self):
        self.laneLinks = [None, None]
        self.notifyVehicles = [None, None]
        self.notifyDistances = [0, 0]
        self.distanceOnLane = [0, 0]
        self.leaveDistance = 0
        self.arriveDistance = 30  # TODO: Initialize to the appropriate value
        self.ang = 0
        self.safeDistances = [0, 0]

    def get_leave_distance(self):
        return self.leaveDistance

    def get_arrive_distance(self):
        return self.arriveDistance

    def notify(self, lane_link: LaneLink, vehicle: Vehicle, notify_distance: float):
        # TODO Implement the notify method logic here
        pass

    def can_pass(self, vehicle: Vehicle, lane_link: LaneLink, distance_to_lane_link_start: float):
        # TODO Implement the canPass method logic here
        pass

    def clear_notify(self):
        self.notifyVehicles = [None, None]

    def get_foe_vehicle(self, lane_link: LaneLink):
        assert lane_link == self.laneLinks[0] or lane_link == self.laneLinks[1]
        return self.notifyVehicles[1] if lane_link == self.laneLinks[0] else self.notifyVehicles[0]

    def get_distance_by_lane(self, lane_link: LaneLink):
        assert lane_link == self.laneLinks[0] or lane_link == self.laneLinks[1]
        return self.distanceOnLane[0] if lane_link == self.laneLinks[0] else self.distanceOnLane[1]

    def get_notify_distance_by_lane(self, lane_link: LaneLink):
        assert lane_link == self.laneLinks[0] or lane_link == self.laneLinks[1]
        return self.notifyDistances[0] if lane_link == self.laneLinks[0] else self.notifyDistances[1]

    def get_safe_distance_by_lane(self, lane_link: LaneLink):
        assert lane_link == self.laneLinks[0] or lane_link == self.laneLinks[1]
        return self.safeDistances[0] if lane_link == self.laneLinks[0] else self.safeDistances[1]

    def get_ang(self):
        return self.ang

    def get_lane_link(self, i):
        return self.laneLinks[i]

    def reset(self):
        # TODO Implement the reset method logic here
        pass
