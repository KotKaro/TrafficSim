from typing import List

from src.roadnet.lane_link import LaneLink
from src.vehicle.vehicle import Vehicle


class Cross:
    def __init__(self):
        self.lane_links: List[LaneLink] = [None, None]
        self.notify_vehicles: List[Vehicle] = [None, None]
        self.notify_distances: List[float] = [0, 0]
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
        assert lane_link == self.lane_links[0] or lane_link == self.lane_links[1]
        index = 0 if lane_link == self.lane_links[0] else 1
        assert self.notify_vehicles[index] is None
        self.notify_vehicles[index] = vehicle
        self.notify_distances[index] = notify_distance

    def can_pass(self, vehicle: Vehicle, lane_link: LaneLink, distance_to_lane_link_start: float):
        assert lane_link in [self.lane_links[0], self.lane_links[1]]
        i = 0 if lane_link == self.lane_links[0] else 1

        foe_vehicle = self.notify_vehicles[1 - i]
        t1 = self.lane_links[i].get_road_link_type()
        t2 = self.lane_links[1 - i].get_road_link_type()
        d1 = self.distance_on_lane[i] - distance_to_lane_link_start
        d2 = self.notify_distances[1 - i]

        if foe_vehicle is None:
            return True

        if not vehicle.can_yield(d1):
            return True

        yield_status = 0
        if not foe_vehicle.can_yield(d2):
            yield_status = 1

        if yield_status == 0:
            if t1 > t2:
                yield_status = -1
            elif t1 < t2:
                if d2 > 0:
                    foe_vehicle_reach_steps = foe_vehicle.get_reach_steps_on_lane_link(d2, self.lane_links[1 - i])
                    reach_steps = vehicle.get_reach_steps_on_lane_link(d1, self.lane_links[i])
                    if foe_vehicle_reach_steps > reach_steps:
                        yield_status = -1
                else:
                    if d2 + foe_vehicle.get_len() < 0:
                        yield_status = -1
                if yield_status == 0:
                    yield_status = 1
            else:
                if d2 > 0:
                    foe_vehicle_reach_steps = foe_vehicle.get_reach_steps_on_lane_link(d2, self.lane_links[1 - i])
                    reach_steps = vehicle.get_reach_steps_on_lane_link(d1, self.lane_links[i])
                    if foe_vehicle_reach_steps > reach_steps:
                        yield_status = -1
                    elif foe_vehicle_reach_steps < reach_steps:
                        yield_status = 1
                    else:
                        if vehicle.get_enter_lane_link_time() == foe_vehicle.get_enter_lane_link_time():
                            if d1 == d2:
                                yield_status = -1 if vehicle.get_priority() > foe_vehicle.get_priority() else 1
                            else:
                                yield_status = -1 if d1 < d2 else 1
                        else:
                            yield_status = -1 if vehicle.get_enter_lane_link_time() < foe_vehicle.get_enter_lane_link_time() else 1
                else:
                    yield_status = -1 if d2 + foe_vehicle.get_len() < 0 else 1

        assert yield_status != 0
        if yield_status == 1:
            fast_pointer = foe_vehicle
            slow_pointer = foe_vehicle
            while fast_pointer is not None and fast_pointer.get_blocker() is not None:
                slow_pointer = slow_pointer.get_blocker()
                fast_pointer = fast_pointer.get_blocker().get_blocker()
                if slow_pointer == fast_pointer:
                    yield_status = -1
                    break

        return yield_status == -1

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
        pass
