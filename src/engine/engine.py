import json
import math
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from typing import List, Dict, Tuple, Set

from src.flow.flow import Flow
from src.flow.route import Route
from src.roadnet.drivable import Drivable
from src.roadnet.intersection import Intersection
from src.roadnet.road import Road
from src.roadnet.roadnet import RoadNet
from src.utility.barrier import Barrier
from src.utility.utility import read_json_from_file, write_json_to_file, min2double
from src.vehicle.vehicle import Vehicle
from src.vehicle.vehicle_info import VehicleInfo


class Engine:
    def __init__(self, config_file: str, thread_num: int):
        self.step: int = 0
        self.activeVehicleCount: int = 0
        self.finished = False
        self.lock = threading.Lock()
        self.interval: float
        self.warnings: bool = False
        self.rlTrafficLight: bool = False
        self.laneChange: bool = False
        self.seed: int
        self.dir: str
        self.road_net: RoadNet
        self.saveReplayInConfig: bool
        self.saveReplay: bool
        self.finished_vehicle_cnt: int = 0
        self.active_vehicle_count: int = 0
        self.cumulative_travel_time: float = 0.0
        self.vehicle_pool: Dict[int, Tuple[Vehicle, int]] = {}
        self.lane_change_notify_buffer: List[Vehicle] = []
        self.push_buffer: List[Tuple[Vehicle, float]] = []

        self.thread_num = thread_num
        self.vehicle_map = Dict[str, Vehicle] = {}
        self.thread_vehicle_pool: List[List[Vehicle]] = [[] for _ in range(thread_num)]
        self.thread_road_pool: List[List[Road]] = [[] for _ in range(thread_num)]
        self.thread_intersection_pool: List[List[Intersection]] = [[] for _ in range(thread_num)]
        self.thread_drivable_pool: List[List[Drivable]] = [[] for _ in range(thread_num)]
        self.flows: List[Flow] = []
        self.start_barrier: Barrier = Barrier(thread_num + 1)
        self.end_barrier: Barrier = Barrier(thread_num + 1)
        self.vehicle_remove_buffer: Set[Vehicle] = set()

        success = self.load_config(config_file)
        if not success:
            print("load config failed!")

        self.thread_pool = ThreadPoolExecutor(max_workers=thread_num)
        self.threads = []
        for i in range(thread_num):
            t = threading.Thread(target=self.thread_controller, args=(
                self.thread_vehicle_pool[i],
                self.thread_road_pool[i],
                self.thread_intersection_pool[i],
                self.thread_drivable_pool[i]))
            self.threads.append(t)
            t.start()

    def thread_controller(self, vehicle_pool, road_pool, intersection_pool, drivable_pool):
        # Thread specific processing logic
        pass

    def load_config(self, config_file: str) -> bool:
        document = read_json_from_file(config_file)
        if read_json_from_file is None:
            print("cannot open config file!")
            return False

        try:
            self.interval = document.interval
            self.warnings = False
            self.rlTrafficLight = document.rlTrafficLight
            self.laneChange = document.laneChange if document.laneChange is not None else False
            self.seed = document.seed
            np.random.seed(self.seed)
            self.dir = document.dir
            roadnet_file: str = document.roadnetFile
            flowFile: str = document.flowFile

            if self.loadRoadNet(self.dir + roadnet_file) is False:
                print("loading roadnet file error!")
                return False

            if self.load_flow(self.dir + flowFile) is False:
                print("loading flow file error!")
                return False

            if self.warnings:
                self.check_warning()

            self.saveReplayInConfig = document.saveReplay
            self.saveReplay = document.saveReplay

            if self.saveReplay:
                roadnetLogFile: str = document.roadnetLogFile
                replayLogFile: str = document.replayLogFile
                self.setLogFile(self.dir + roadnetLogFile, self.dir + replayLogFile)
        except:
            return False
        self.stepLog = ""
        return True

    def loadRoadNet(self, json_file: str) -> bool:
        self.road_net = RoadNet()
        ans = self.road_net.load_from_json(json_file)
        cnt = 0
        for road in self.road_net.get_roads():
            self.thread_road_pool[cnt].append(road)
            cnt = (cnt + 1) % self.thread_num

        for intersection in self.road_net.get_intersections():
            self.thread_intersection_pool[cnt].append(intersection)
            cnt = (cnt + 1) % self.thread_num

        for drivable in self.road_net.get_drivables():
            self.thread_drivable_pool[cnt].append(drivable)
            cnt = (cnt + 1) % self.thread_num

        self.json_root = self.road_net.convert_to_json()
        return ans

    def load_flow(self, json_filename: str):
        try:
            root = read_json_from_file(json_filename)

            if not isinstance(root, list):
                raise TypeError("flow file must be an array")

            for i, flow in enumerate(root):
                roads = Route()
                for road_name in flow["route"]:
                    if not isinstance(road_name, str):
                        raise TypeError("route must be a string")
                    road = self.road_net.get_road_by_id(road_name)
                    if not road:
                        raise ValueError(f"No such road: {road_name}")
                    roads.route.append(road)

                vehicle_info = VehicleInfo()
                vehicle_info.len = flow["vehicle"]["length"]
                vehicle_info.width = flow["vehicle"]["width"]
                vehicle_info.max_pos_acc = flow["vehicle"]["maxPosAcc"]
                vehicle_info.max_neg_acc = flow["vehicle"]["maxNegAcc"]
                vehicle_info.usual_pos_acc = flow["vehicle"]["usualPosAcc"]
                vehicle_info.usual_neg_acc = flow["vehicle"]["usualNegAcc"]
                vehicle_info.min_gap = flow["vehicle"]["minGap"]
                vehicle_info.max_speed = flow["vehicle"]["maxSpeed"]
                vehicle_info.headway_time = flow["vehicle"]["headwayTime"]
                vehicle_info.route = roads

                start_time = flow.get("startTime", 0)
                end_time = flow.get("endTime", -1)

                new_flow = Flow(
                    vehicleInfo=vehicle_info,
                    time_interval=flow["interval"],
                    engine=self,
                    start_time=start_time,
                    end_time=end_time,
                    id=f"flow_{i}"
                )

                self.flows.append(new_flow)

        except (IOError, json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"Error occurred when reading flow file: {e}")
            return False

        return True

    def check_warning(self):
        result = True

        if self.interval < 0.2 or self.interval > 1.5:
            print("Deprecated time interval, recommended interval between 0.2 and 1.5")
            result = False

        for lane in self.road_net.get_lanes():
            if lane.get_length() < 50:
                print("Deprecated road length, recommended road length at least 50 meters")
                result = False

            if lane.get_max_speed() > 30:
                print("Deprecated road max speed, recommended max speed at most 30 meters/s")
                result = False

        return result

    def vehicle_control(self, vehicle: Vehicle, buffer: List[Tuple[Vehicle, float]]) -> None:

        next_speed = vehicle.get_buffer_speed() if vehicle.has_set_speed() else vehicle.get_next_speed(
            self.interval).speed

        if self.laneChange:
            partner = vehicle.get_partner()
            if partner is not None and partner.has_set_speed() is False:
                partner_speed = partner.get_next_speed(self.interval).speed
                next_speed = min(next_speed, partner_speed)
                partner.set_speed(next_speed)

                if partner.has_set_end():
                    vehicle.set_end(True)

        if vehicle.get_partner():
            assert vehicle.get_distance() == vehicle.get_partner().get_distance()

        speed = vehicle.get_speed()

        if next_speed < 0:
            delta_dis = 0.5 * speed * speed / vehicle.get_max_neg_acc()
            next_speed = 0
        else:
            delta_dis = (speed + next_speed) * self.interval / 2

        vehicle.set_speed(next_speed)
        vehicle.set_delta_distance(delta_dis)

        if self.laneChange:
            if vehicle.is_real() and vehicle.get_changed_drivable() is not None:
                vehicle.abort_lane_change()

            if vehicle.is_changing():
                assert vehicle.is_real()

                direction = vehicle.get_lane_change_direction()
                new_offset = math.fabs(vehicle.get_offset() + max(0.2 * next_speed, 1) * self.interval * direction)
                new_offset = min(new_offset, vehicle.get_max_offset())
                vehicle.set_offset(new_offset * direction)

                if new_offset >= vehicle.get_max_offset():
                    with self.lock:
                        del self.vehicle_map[vehicle.get_partner().get_id()]
                        self.vehicle_map[vehicle.get_id()] = vehicle.get_partner()
                        vehicle.finish_changing()

        if vehicle.has_set_end() is False and vehicle.has_set_drivable():
            buffer.append((vehicle, vehicle.get_buffer_dis()))

    def threadController(self, vehicles: Set[Vehicle],
                         roads: List[Road],
                         intersections: List[Intersection],
                         drivables: List[Drivable]) -> None:
        while self.finished is False:
            self.thread_plan_route(roads)
            if self.laneChange:
                self.thread_init_segments(roads)
                self.thread_plan_lane_change(vehicles)
                self.thread_update_leader_and_gap(drivables)

            self.thread_notify_cross(intersections)
            self.thread_get_action(vehicles)
            self.thread_update_location(drivables)
            self.thread_update_action(vehicles)
            self.thread_update_leader_and_gap(drivables)

    def thread_update_location(self, drivables: List[Drivable]) -> None:
        self.start_barrier.wait()
        for drivable in drivables:
            drivable.vehicles = [vehicle for vehicle in drivable.vehicles if
                                 vehicle.get_changed_drivable() is not None or vehicle.has_set_end()]
            vehicles = drivable.get_vehicles()
            vehicle_iter = iter(vehicles)
            while True:
                try:
                    vehicle = next(vehicle_iter)
                except StopIteration:
                    break

                if vehicle.get_changed_drivable() or vehicle.has_set_end():
                    vehicles.remove(vehicle)

                if vehicle.has_set_end():
                    with self.lock:
                        self.vehicle_remove_buffer.add(vehicle)
                        if vehicle.lane_change.has_finished():
                            del self.vehicle_map[vehicle.get_id]

                            self.finished_vehicle_cnt += 1
                            self.cumulative_travel_time += self.get_current_time() - vehicle.enter_time

                        iter_vehicle_pool = self.vehicle_pool[vehicle.get_priority()]
                        self.thread_vehicle_pool[iter_vehicle_pool[1]].remove(vehicle)
                        del self.vehicle_pool[vehicle.get_priority()]
                        self.active_vehicle_count -= 1
        self.end_barrier.wait()

    def thread_notify_cross(self, intersections: List[Intersection]) -> None:
        self.start_barrier.wait()

        for intersection in intersections:
            for cross in intersection.get_crosses():
                cross.clear_notify()

        for intersection in intersections:
            for lane_link in intersection.get_lane_links():
                crosses = list(reversed(lane_link.get_crosses()))
                r_iter = iter(crosses)

                vehicle = lane_link.get_end_lane().get_last_vehicle()
                if vehicle and vehicle.get_prev_drivable() == lane_link:
                    veh_distance = vehicle.get_distance() - vehicle.get_len()

                    while True:
                        try:
                            cross = next(r_iter)
                            cross_distance = lane_link.get_length() - cross.get_distance_by_lane(lane_link)
                            if cross_distance + veh_distance < cross.get_leave_distance():
                                cross.notify(lane_link, vehicle, -(vehicle.get_distance() + cross_distance))
                            else:
                                break
                        except StopIteration:
                            break

                for link_vehicle in lane_link.get_vehicles():
                    veh_distance = link_vehicle.get_distance()

                    while True:
                        try:
                            cross = next(r_iter)
                            cross_distance = cross.get_distance_by_lane(lane_link)
                            if veh_distance > cross_distance:
                                if veh_distance - cross_distance - link_vehicle.get_len() <= cross.get_leave_distance():
                                    cross.notify(lane_link, link_vehicle, cross_distance - veh_distance)
                                else:
                                    break
                            else:
                                cross.notify(lane_link, link_vehicle, cross_distance - veh_distance)
                        except StopIteration:
                            break

                vehicle = lane_link.get_start_lane().get_first_vehicle()
                if vehicle and vehicle.get_next_drivable() == lane_link and lane_link.is_available():
                    veh_distance = lane_link.get_start_lane().get_length() - vehicle.get_distance()
                    while True:
                        try:
                            cross = next(r_iter)
                            cross.notify(lane_link, vehicle, veh_distance + cross.get_distance_by_lane(lane_link))
                        except StopIteration:
                            break

        self.end_barrier.wait()

    def thread_plan_lane_change(self, vehicles: Set[Vehicle]) -> None:
        self.start_barrier.wait()
        buffer: List[Vehicle] = [];

        for vehicle in vehicles:
            if vehicle.is_running() and vehicle.is_real():
                vehicle.make_lane_change_signal(self.interval)
                if vehicle.plan_lane_change():
                    buffer.append(vehicle)

        with self.lock:
            self.lane_change_notify_buffer.extend(buffer)
        self.end_barrier.wait()

    def thread_init_segments(self, roads: List[Road]) -> None:
        self.start_barrier.wait()
        for road in roads:
            for lane in road.get_lanes():
                lane.initSegments()

        self.end_barrier.wait()

    def thread_get_action(self, vehicles: Set[Vehicle]) -> None:
        self.start_barrier.wait()
        buffer: List[Tuple[Vehicle, float]] = []
        for vehicle in vehicles:
            if vehicle.is_running():
                self.vehicle_control(vehicle, buffer)

        with self.lock:
            self.push_buffer.extend(buffer)

        self.end_barrier.wait()

    def thread_update_action(self, vehicles: Set[Vehicle]) -> None:
        self.start_barrier.wait()
        for vehicle in vehicles:
            if vehicle.is_running():
                if vehicle.get_buffer_blocker() in self.vehicle_remove_buffer:
                    vehicle.set_blocker(None)

                vehicle.update()
                vehicle.clear_signal()

        self.end_barrier.wait()

    def thread_update_leader_and_gap(self, drivables: List[Drivable]) -> None:
        self.start_barrier.wait()
        for drivable in drivables:
            leader: Vehicle | None = None
            for vehicle in drivable.get_vehicles():
                vehicle.update_leader_and_gap(leader)
                leader = vehicle

            if drivable.is_lane():
                drivable.update_history()
        self.end_barrier.wait()

    def plan_lane_change(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()
        self.scheduleLaneChange()

    def plan_route(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()

        for road in self.road_net.get_roads():
            for vehicle in road.get_plan_route_buffer():
                if vehicle.is_route_valid():
                    vehicle.set_first_drivable()
                    vehicle.get_cur_lane().push_waiting_vehicle(vehicle)
                else:
                    flow = vehicle.flow
                    if flow is not None:
                        flow.setValid(False)

                    iter_vehicle = self.vehicle_pool[vehicle.get_priority()]
                    self.thread_vehicle_pool[iter_vehicle[1]].remove(vehicle)
                    del self.vehicle_pool[vehicle.get_priority()]

            road.clear_plan_route_buffer()

    def get_action(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()

    def update_location(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()

        self.push_buffer.sort(key=lambda x: x[1])
        for vehicle_pair in self.push_buffer:
            vehicle, drivable = vehicle_pair
            changed_drivable = vehicle.get_changed_drivable()
            if changed_drivable:
                changed_drivable.push_vehicle(vehicle)
                if changed_drivable.is_lane_link():
                    vehicle.set_enter_lane_link_time(self.step)
                else:
                    vehicle.set_enter_lane_link_time(sys.maxsize)

        self.push_buffer.clear()

    def update_action(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()
        self.vehicle_remove_buffer.clear()


    def handle_waiting(self) -> None:
        for lane in self.road_net.get_lanes():
            buffer = lane.get_waiting_buffer()
            if len(buffer) == 0:
                continue

            vehicle = buffer[0]
            if lane.available(vehicle):
                vehicle.controller_info.running = True
                self.activeVehicleCount += 1
                tail = lane.get_last_vehicle()
                lane.push_vehicle(vehicle)
                vehicle.update_leader_and_gap(tail)
                buffer.popleft()

    def rnd(self):
        pass

    def check_priority(self, priority: int):
        self.thread_vehicle_pool[priority] is not self.thread_vehicle_pool[-1]

    def pushVehicle(self, vehicle: Vehicle, pushToDrivable: bool):
        pass

    def get_current_time(self) -> float:
        pass

    def get_interval(self) -> float:
        pass

    def setLogFile(self, json_file: str, log_file: str):
        if write_json_to_file(json_file, self.json_root) is False:
            print("write roadnet log file error")
        open(log_file, 'w')
