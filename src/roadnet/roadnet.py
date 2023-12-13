import json
from typing import Dict, List

from src.roadnet.drivable import Drivable
from src.roadnet.intersection import Intersection
from src.roadnet.lane import Lane
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road
from src.roadnet.road_link import RoadLinkType, RoadLink
from src.roadnet.traffic_light import LightPhase
from src.utility.config import CityFlow
from src.utility.utility import Point
from src.vehicle.vehicle_info import VehicleInfo


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

    def load_from_json(self, json_file_name) -> bool:
        with open(json_file_name, 'r') as file:
            document = json.load(file)

        # Check if the document is an object
        if not isinstance(document, dict):
            raise TypeError("roadnet config file should be an object")

        inter_values = document["intersections"]
        road_values = document["roads"]

        self._roads.clear()
        for index, road in enumerate(road_values):
            self._road_map[road["id"]] = road
            self._roads[index] = Road(road["id"])

        for index, intersection in enumerate(inter_values):
            self._inter_map[intersection["id"]] = intersection
            self._intersections[index] = Intersection(intersection["id"])

        for i, cur_road_value in enumerate(road_values):
            if not isinstance(cur_road_value, dict):
                raise TypeError(f"road[{i}] should be an object")

            start_intersection_id = cur_road_value.get("startIntersection")
            end_intersection_id = cur_road_value.get("endIntersection")

            road_values[i].start_intersection = self._inter_map.get(start_intersection_id)
            road_values[i].end_intersection = self._inter_map.get(end_intersection_id)

            if not self._roads[i].start_intersection:
                raise ValueError("startIntersection does not exist.")
            if not self._roads[i].end_intersection:
                raise ValueError("endIntersection does not exist.")

            lanes_value = cur_road_value.get("lanes", [])
            for lane_index, lane_value in enumerate(lanes_value):
                if not isinstance(lane_value, dict):
                    raise TypeError("lane should be an object")

                width = lane_value.get("width")
                max_speed = lane_value.get("maxSpeed")
                self._roads[i].lanes.append(Lane(width, max_speed, lane_index, self._roads[i]))

            for lane in self._roads[i].lanes:
                self._drivable_map[lane.get_id()] = lane

            # Read points
            points_value = cur_road_value.get("points", [])
            for point_value in points_value:
                if not isinstance(point_value, dict):
                    raise TypeError("point of road should be an object")

                x = point_value.get("x")
                y = point_value.get("y")
                self._roads[i].points.append(Point(x, y))

        for road in self._roads:
            road.init_lanes_points()

        typeMap: Dict[str, RoadLinkType] = {'turn_left': RoadLinkType.turn_left,
                                            "turn_right": RoadLinkType.turn_right,
                                            "go_straight": RoadLinkType.go_straight}

        for i in range(len(inter_values)):
            curInterValue = inter_values[i]
            if not isinstance(curInterValue, dict):
                raise TypeError(f"intersection[{i}] should be an object")

            pointValue = curInterValue["point"]
            self._intersections[i].is_virtual = curInterValue["virtual"]
            self._intersections[i].point = Point(pointValue["x"], pointValue["y"])

            for roadNameValue in curInterValue["roads"]:
                roadName = roadNameValue
                if roadName in self._road_map:
                    raise TypeError("No such road: " + roadName)

                self._intersections[i].roads.append(self._road_map[roadName])

            self._intersections[i].trafficLight.intersection = self._intersections[i]
            self._intersections[i].width = curInterValue.width
            self._intersections[i].road_links.clear()

            roadLinkIndex = 0
            for roadLinkValue in curInterValue["roadLinks"]:
                roadLink = RoadLink()
                roadLink.index = roadLinkIndex
                roadLinkIndex += 1

                roadLink.type = typeMap.get(roadLinkValue.type)
                roadLink.startRoad = roadLinkValue.startRoad
                roadLink.endRoad = roadLinkValue.endRoad
                self._intersections[i].road_links.append(roadLink)

                roadLink.lane_links.clear()
                laneLinkIndex = 0
                for laneLinkValue in roadLinkValue.laneLinks:
                    if not isinstance(roadLinkIndex, dict):
                        raise TypeError("laneLink should be an object")

                    lane_link = LaneLink()  # Assuming a LaneLink class exists
                    roadLink.lane_links.append(lane_link)
                    roadLinkIndex += 1

                    start_lane_index = laneLinkValue.get("startLaneIndex")
                    end_lane_index = laneLinkValue.get("endLaneIndex")
                    if not 0 <= start_lane_index < len(roadLink.start_road.lanes):
                        raise ValueError("startLaneIndex out of range")
                    if not 0 <= end_lane_index < len(roadLink.end_road.lanes):
                        raise ValueError("endLaneIndex out of range")

                    start_lane: Lane = roadLink.start_road.lanes[start_lane_index]
                    end_lane: Lane = roadLink.end_road.lanes[end_lane_index]

                    if "points" in roadLinkValue:
                        points = roadLinkValue["points"]
                        if not isinstance(points, list):
                            raise TypeError("points in laneLink should be an array")
                        for p_value in points:
                            lane_link.points.append(Point(p_value["x"], p_value["y"]))  # Assuming a Point class exists
                    else:
                        start = Point(start_lane.get_point_by_distance(
                            start_lane.get_length() - start_lane.get_end_intersection().width))
                        end = Point(end_lane.get_point_by_distance(0.0 + end_lane.get_start_intersection().width))
                        len = (Point(end.x - start.x, end.y - start.y)).len()
                        startDirection = start_lane.get_direction_by_distance(
                            start_lane.get_length() - start_lane.get_end_intersection().width)
                        endDirection = end_lane.get_direction_by_distance(0.0 + end_lane.get_start_intersection().width)
                        minGap = 5
                        gap1X = startDirection.x * len * 0.5
                        gap1Y = startDirection.y * len * 0.5
                        gap2X = -endDirection.x * len * 0.5
                        gap2Y = -endDirection.y * len * 0.5
                        if gap1X * gap1X + gap1Y * gap1Y < 25 and start_lane.get_end_intersection().width >= 5:
                            gap1X = minGap * startDirection.x
                            gap1Y = minGap * startDirection.y
                        if gap2X * gap2X + gap2Y * gap2Y < 25 and end_lane.get_start_intersection().width >= 5:
                            gap2X = minGap * endDirection.x
                            gap2Y = minGap * endDirection.y
                        mid1 = Point(start.x + gap1X, start.y + gap1Y)
                        mid2 = Point(end.x + gap2X, end.y + gap2Y)
                        numPoints = 10.0
                        for y in range(int(numPoints + 1)):
                            p1 = self.get_point(start, mid1, y / numPoints)
                            p2 = self.get_point(mid1, mid2, y / numPoints)
                            p3 = self.get_point(mid2, end, y / numPoints)
                            p4 = self.get_point(p1, p2, y / numPoints)
                            p5 = self.get_point(p2, p3, y / numPoints)
                            p6 = self.get_point(p4, p5, y / numPoints)
                            lane_link.points.append(p6.x, p6.y)

                    lane_link.road_link = roadLink
                    lane_link.start_lane = start_lane
                    lane_link.end_lane = end_lane
                    lane_link.length = Point.get_length_of_points(lane_link.points)
                    start_lane.lane_links.append(lane_link)
                    self._drivable_map[lane_link.get_id()] = lane_link

            for lightPhaseValue in curInterValue.trafficLight.lightphases:
                if not isinstance(lightPhaseValue, dict):
                    raise TypeError("lightphase should be an object")

                lightPhase = LightPhase()
                lightPhase.time = lightPhaseValue.get("time")
                lightPhase.road_link_available = [False] * len(self._intersections[i].road_links)

                availableRoadLinksValue = lightPhaseValue.get("availableRoadLinks")
                if not isinstance(availableRoadLinksValue, list):
                    raise TypeError("availableRoadLinks in lightphase should be an array")

                for index in availableRoadLinksValue:
                    if not isinstance(index, int):
                        raise TypeError("availableRoadLink should be an int")
                    if index >= len(lightPhase.road_link_available):
                        raise ValueError("index out of range")
                    lightPhase.road_link_available[index] = True

                self._intersections[i].traffic_light.phases.append(lightPhase)

            self._intersections[i].traffic_light.init(0)

        for intersection in self._intersections:
            intersection.init_crosses()

        vehicleTemplate = VehicleInfo()

        for road in self._roads:
            road.init_lanes_points()

        for road in self._roads:
            road.build_segmentation_by_interval(
                (vehicleTemplate.len + vehicleTemplate.minGap) * CityFlow.MAX_NUM_CARS_ON_SEGMENT)

        for road in self._roads:
            roadLanes = road.get_lane_pointers()
            self._lanes.extend(roadLanes)
            self._drivables.extend(roadLanes)

        for intersection in self._intersections:
            intersectionLaneLinks = intersection.get_lane_links()
            self._lane_links.extend(intersectionLaneLinks)
            self._drivables.extend(intersectionLaneLinks)

        return True

    def convert_to_json(self):
        return {
            "nodes": list(map(lambda intersection: {
                "id": intersection.id,
                "point": [intersection.point.x, intersection.point.y],
                "virtual": intersection.is_virtual,
                "outline": [coordinate for point in intersection.get_outline() for coordinate in (point.x, point.y)],
                **({
                       "width": intersection.width} if not intersection.is_virtual and intersection.width is not None else {})
            }, self._intersections)),
            "edges": list(map(self._roads, lambda road: {
                "id": road.id,
                "from": road.start_intersection.id if road.start_intersection else "null",
                "to": road.end_intersection.id if road.end_intersection else "null",
                "points": [[point.x, point.y] for point in road.points],
                "nLane": len(road.lanes),
                "laneWidths": [lane.width for lane in road.lanes]
            }))
        }

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
