from src.roadnet.lane_link import LaneLink
from src.vehicle.vehicle import Vehicle


class Cross:
    def __init__(self):
        self.lane_links = [None, None]
        self.notify_vehicles = [None, None]
        self.notify_distances = [0, 0]
        self.distance_on_lane = [0, 0]
        self.leave_distance = 0
        self.arrive_distance = 30  # TODO: Initialize to the appropriate value
        self.ang = 0
        self.safe_distances = [0, 0]

    def get_leave_distance(self):
        return self.leave_distance

    def get_arrive_distance(self):
        return self.arrive_distance

    def notify(self, lane_link: LaneLink, vehicle: Vehicle, notify_distance: float):
        # TODO Implement the notify method logic here
        pass

    def can_pass(self, vehicle: Vehicle, lane_link: LaneLink, distance_to_lane_link_start: float):
        # TODO Implement the canPass method logic here
        pass

    def clear_notify(self):
        self.notify_vehicles = [None, None]

    def get_foe_vehicle(self, lane_link: LaneLink):
        assert lane_link == self.lane_links[0] or lane_link == self.lane_links[1]
        return self.notify_vehicles[1] if lane_link == self.lane_links[0] else self.notify_vehicles[0]

    def get_distance_by_lane(self, lane_link: LaneLink):
        assert lane_link == self.lane_links[0] or lane_link == self.lane_links[1]
        return self.distance_on_lane[0] if lane_link == self.lane_links[0] else self.distance_on_lane[1]

    def get_notify_distance_by_lane(self, lane_link: LaneLink):
        assert lane_link == self.lane_links[0] or lane_link == self.lane_links[1]
        return self.notify_distances[0] if lane_link == self.lane_links[0] else self.notify_distances[1]

    def get_safe_distance_by_lane(self, lane_link: LaneLink):
        assert lane_link == self.lane_links[0] or lane_link == self.lane_links[1]
        return self.safe_distances[0] if lane_link == self.lane_links[0] else self.safe_distances[1]

    def get_ang(self):
        return self.ang

    def get_lane_link(self, i):
        return self.lane_links[i]

    def reset(self):
        # TODO Implement the reset method logic here
        pass
