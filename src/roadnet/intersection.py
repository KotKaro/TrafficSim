import math
from typing import List

from src.roadnet.cross import Cross
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road
from src.roadnet.road_link import RoadLink
from src.roadnet.traffic_light import TrafficLight
from src.utility.utility import Point, cross_multiply, on_segment, calc_ang, calc_intersect_point


class Intersection:
    def __init__(self, id: str, is_virtual: bool, width: float, point: Point, traffic_light: TrafficLight,
                 roads: List[Road],
                 road_links: List[RoadLink], crosses: List[Cross], lane_links: List[LaneLink]):
        self.id: str = id
        self.is_virtual: bool = is_virtual
        self.width: float = width
        self.point: Point = point
        self.traffic_light: TrafficLight = traffic_light
        self.roads: List[Road] = roads
        self.road_links: List[RoadLink] = road_links
        self.crosses: List[Cross] = crosses
        self.lane_links: List[LaneLink] = lane_links

    def get_id(self) -> str:
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
            road_lane_links = road_link.lane_links
            self.lane_links.extend(road_lane_links)

        return self.lane_links

    def reset(self) -> None:
        self.traffic_light.reset()
        for roadLink in self.road_links:
            roadLink.reset()
        for cross in self.crosses:
            cross.reset()

    def get_outline(self) -> List[Point]:
        points = [self.point]
        for road in self.get_roads():
            road_direct = road.get_end_intersection().get_position() - road.get_start_intersection().point
            road_direct = road_direct.unit()
            p_direct = road_direct.normal()
            if road.get_start_intersection() == self:
                road_direct = -road_direct

            road_width = road.get_width()
            delta_width = 0.5 * min(self.width, road_width)
            delta_width = max(delta_width, 5)

            point_a = self.point - road_direct * self.width
            point_b = point_a - p_direct * road_width
            points.append(point_a)
            points.append(point_b)

            if delta_width < road.average_length():
                point_a1 = point_a - road_direct * delta_width
                point_b1 = point_b - road_direct * delta_width
                points.append(point_a1)
                points.append(point_b1)

        # Sorting points based on y-coordinate
        points.sort(key=lambda point: point.y)

        p0 = points[0]
        stack = [p0]
        points.remove(p0)

        # Sorting remaining points based on angle with p0
        points.sort(key=lambda point: (point - p0).ang())

        for point in points:
            p2 = stack[-1]
            if len(stack) < 2:
                if point.x != p2.x or point.y != p2.y:
                    stack.append(point)
                continue
            p1 = stack[-2]

            while len(stack) > 1 and cross_multiply(point - p2, p2 - p1) >= 0:
                p2 = p1
                stack.pop()
                if len(stack) > 1:
                    p1 = stack[-2]

            stack.append(point)

        return stack

    def is_implicit_intersection(self):
        return len(self.traffic_light.get_phases()) <= 1

    def init_crosses(self):
        all_lane_links = [lane_link for road_link in self.road_links for lane_link in road_link.lane_links]
        n = len(all_lane_links)

        for i in range(n):
            for j in range(i + 1, n):
                la = all_lane_links[i]
                lb = all_lane_links[j]
                va = la.points
                vb = lb.points
                disa = 0.0

                for ia in range(len(va) - 1):
                    disb = 0.0
                    for ib in range(len(vb) - 1):
                        a1, a2 = va[ia], va[ia + 1]
                        b1, b2 = vb[ib], vb[ib + 1]

                        if Point.sign(cross_multiply(a2 - a1, b2 - b1)) == 0:
                            continue

                        p = calc_intersect_point(a1, a2, b1, b2)

                        if on_segment(a1, a2, p) and on_segment(b1, b2, p):
                            cross = Cross()
                            cross.lane_links[0] = la
                            cross.lane_links[1] = lb
                            cross.notify_vehicles = [None, None]
                            cross.distance_on_lane = [
                                disa + (p - a1).length(),
                                disb + (p - b1).length()
                            ]
                            cross.ang = calc_ang(a2 - a1, b2 - b1)

                            w1, w2 = la.get_width(), lb.get_width()
                            c1, c2 = w1 / math.sin(cross.ang), w2 / math.sin(cross.ang)
                            diag = (c1 ** 2 + c2 ** 2 + 2 * c1 * c2 * math.cos(cross.ang)) / 4
                            cross.safe_distances = [
                                math.sqrt(diag - w2 ** 2 / 4),
                                math.sqrt(diag - w1 ** 2 / 4)
                            ]
                            self.crosses.append(cross)
                            break

                        disb += (vb[ib + 1] - vb[ib]).length()

                    disa += (va[ia + 1] - va[ia]).length()

        for cross in self.crosses:
            cross.lane_links[0].get_crosses().append(cross)
            cross.lane_links[1].get_crosses().append(cross)

        for lane_link in all_lane_links:
            crosses = lane_link.get_crosses()
            crosses.sort(key=lambda c: c.distance_on_lane[0 if c.lane_links[0] != lane_link else 1])
