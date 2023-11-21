import sys
from collections import deque
from random import Random
from typing import List, Deque

from src.flow.route import Route
from src.roadnet.drivable import Drivable
from src.roadnet.lane import Lane
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road
from src.vehicle.vehicle import Vehicle


class Router:
    def __init__(self, other: 'Router' = None, vehicle: Vehicle = None, route: Route = None, rnd: Random = None):
        if other:
            self.vehicle: Vehicle = other.vehicle
            self.route: List[Road] = other.route
            self.anchor_points: List[Road] = self.anchor_points
            self.rnd: Random = other.rnd
        else:
            self.vehicle: Vehicle = vehicle
            self.anchor_points: List[Road] = route.get_route()
            self.rnd: Random = rnd
            assert len(self.anchor_points) > 0
            self.route = route.get_route()

        self.i_cur_road: Road = self.route[0]
        self.planned: Deque[Drivable] = deque()

    def get_first_drivable(self) -> Drivable:
        lanes: List[Lane] = self.route[0].get_lane_pointers()
        if len(self.route) == 1:
            return self.select_lane(cur_lane=None, lanes=lanes)
        else:
            candidateLanes: List[Lane] = []
            for lane in lanes:
                if len(lane.get_lane_links_to_road(self.route[1])) > 0:
                    candidateLanes.append(lane)

        assert len(candidateLanes) > 0
        return self.select_lane(cur_lane=None, lanes=candidateLanes)

    def get_next_drivable(self, i: int = None, curr_drivable: LaneLink | Lane = None) -> Drivable | None:
        if i is not None:
            if i < len(self.planned):
                return self.planned[i]
            else:
                ret: Drivable = self.get_next_drivable(
                    curr_drivable=self.planned[-1]
                    if len(self.planned) > 0
                    else self.vehicle.get_cur_drivable()
                )
                self.planned.append(ret)
                return ret
        else:
            if curr_drivable.is_lane_link():
                curr_drivable: LaneLink = curr_drivable
                return curr_drivable.get_end_lane()
            else:
                cur_lane: Lane = curr_drivable
                tmpCurRoad: Road = self.i_cur_road

                while tmpCurRoad is not cur_lane.belong_road and tmpCurRoad is not self.route[-1]:
                    tmpCurRoad = self.route[self.route.index(tmpCurRoad) + 1]

                assert (tmpCurRoad is not self.route[-1] and cur_lane.belong_road == tmpCurRoad)

                if tmpCurRoad == self.route[-2]:
                    return None
                elif tmpCurRoad == self.route[-3]:
                    lane_links = cur_lane.get_lane_links_to_road(self.route[self.route.index(self.i_cur_road) + 1])
                    return self.select_lane_link(cur_lane, lane_links)
                else:
                    lane_links = cur_lane.get_lane_links_to_road(self.route[self.route.index(self.i_cur_road) + 1])
                    candidateLaneLinks = [a for a in lane_links if len(a.get_end_lane().get_lane_links_to_road(
                        self.route[self.route.index(tmpCurRoad) + 2])) > 0]
                    return self.select_lane_link(cur_lane, candidateLaneLinks)

    def select_lane_link(self, cur_lane: Lane, lane_links: List[LaneLink]) -> LaneLink | None:
        if len(lane_links) == 0:
            return None

        return lane_links[self.select_lane_index(cur_lane, [x.get_end_lane() for x in lane_links])]

    def set_vehicle(self, vehicle: Vehicle):
        self.vehicle = vehicle

    def update(self) -> None:
        cur_drivable = self.vehicle.get_cur_drivable()
        if cur_drivable.is_lane():
            cur_drivable: Lane = cur_drivable
            while self.route.index(self.i_cur_road) < len(self.route) and cur_drivable.belong_road != self.route[
                self.route.index(self.i_cur_road)]:
                self.i_cur_road = self.route[self.route.index(self.i_cur_road) + 1]
            assert self.route.index(self.i_cur_road) < len(self.route)

        self.planned = [drivable for drivable in self.planned if drivable == cur_drivable]

    def is_last_road(self, drivable: Drivable) -> bool:
        if drivable.is_lane_link():
            return False
        return drivable.belong_road == self.route[-1]

    def on_last_road(self) -> bool:
        return self.is_last_road(self.vehicle.get_cur_drivable())

    def select_lane_index(self, cur_lane: Lane, lanes: List[Lane]) -> int:
        assert len(lanes) > 0
        if cur_lane is None:
            return self.rnd.randint(0, len(lanes) - 1)

        lane_diff: int = sys.maxsize
        selected: int = -1

        for i in range(len(lanes)):
            cur_lane_diff: int = lanes[i].lane_index - cur_lane.lane_index
            if abs(cur_lane_diff) < lane_diff:
                lane_diff = abs(cur_lane_diff)
                selected = i

        return selected

    def select_lane(self, cur_lane: Lane | None, lanes: List[Lane]):
        if len(lanes) == 0:
            return None

        return lanes[self.select_lane_index(cur_lane, lanes)]
