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
        self.log_out = None
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
        self.saveReplay: bool = False
        self.finished_vehicle_cnt: int = 0
        self.active_vehicle_count: int = 0
        self.cumulative_travel_time: float = 0.0
        self.vehicle_pool: Dict[int, Tuple[Vehicle, int]] = {}
        self.lane_change_notify_buffer: List[Vehicle] = []
        self.push_buffer: List[Tuple[Vehicle, float]] = []

        self.thread_num = thread_num
        self.vehicle_map: Dict[str, Vehicle] = {}
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

    def __del__(self):
        self.log_out.close()
        self.finished = True

        for i in range((9 if self.laneChange else 6)):
            self.start_barrier.wait()
            self.end_barrier.wait()

        for thread in self.thread_pool:
            thread.join()

        for vehicle_pair in self.vehicle_pool.values():
            del vehicle_pair[0]

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

    def update_log(self):
        result = ""
        for vehicle in self.get_running_vehicles():
            pos = vehicle.get_point()
            dir = vehicle.get_cur_drivable().get_direction_by_distance(vehicle.get_distance())

            lc = vehicle.last_lane_change_direction()
            result += (
                f"{pos.x} {pos.y} {math.atan2(dir.y, dir.x)} "
                f"{vehicle.get_id()} {lc} {vehicle.get_len()} "
                f"{vehicle.get_width()},"
            )
        result += ";"

        for road in self.roadnet.get_roads():
            if road.get_end_intersection().is_virtual_intersection():
                continue
            result += road.get_id()
            for lane in road.get_lanes():
                if lane.get_end_intersection().is_implicit_intersection():
                    result += " i"
                    continue

                can_go = all(lane_link.is_available() for lane_link in lane.get_lane_links())
                result += " g" if can_go else " r"
            result += ","

        with open('logfile.txt', 'w') as log_out:  # Replace 'logfile.txt' with actual log file's path
            log_out.write(f"{result}\n")

    def update_leader_and_gap(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()

    def notify_cross(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()

    def nextStep(self) -> None:
        for flow in self.flows:
            flow.nextStep(self.interval)

        self.plan_route()
        self.handle_waiting()

        if (self.laneChange):
            self.init_segments()
            self.plan_lane_change()
            self.update_leader_and_gap()

        self.notify_cross()

        self.get_action()
        self.update_location()
        self.update_action()
        self.update_leader_and_gap()

        if self.rlTrafficLight is None:
            intersections = self.road_net.get_intersections()
            for intersection in intersections:
                intersection.get_traffic_light().pass_time(self.interval)

        if self.saveReplay:
            self.update_log()

        self.step += 1

    def init_segments(self) -> None:
        self.start_barrier.wait()
        self.end_barrier.wait()

    def check_priority(self, priority: int) -> bool:
        return self.vehicle_pool[priority] != self.vehicle_pool[-1]

    def push_vehicle(self, vehicle: Vehicle, push_to_drivable: bool) -> None:
        threadIndex = np.random.randint(1, self.thread_num)
        self.vehicle_pool[vehicle.get_priority()] = (vehicle, threadIndex)
        self.vehicle_map[vehicle.get_id()] = vehicle
        self.thread_vehicle_pool[threadIndex].append(vehicle)

        if push_to_drivable:
            vehicle.get_cur_drivable().push_waiting_vehicle(vehicle)

    def get_vehicle_count(self) -> int:
        return self.activeVehicleCount

    def get_vehicles(self, include_waiting) -> List[str]:
        ret = []
        for vehicle in self.get_running_vehicles(include_waiting):  # Replace with your function call or attribute
            ret.append(vehicle.get_id())
        return ret

    def get_lane_vehicle_count(self) -> Dict[str, int]:
        ret: Dict[str, int] = {}
        for lane in self.road_net.get_lanes():
            ret[lane.get_id()] = lane.get_vehicle_count()
        return ret

    def get_lane_waiting_vehicle_count(self) -> Dict[str, int]:
        ret: Dict[str, int] = {}

        for lane in self.road_net.get_lanes():
            cnt = 0;
            for vehicle in lane.get_vehicles():
                if vehicle.get_speed() < 0.1:
                    cnt += 1;

            ret[lane.get_id()] = cnt
        return ret

    def get_lane_vehicles(self) -> Dict[str, List[str]]:
        ret: Dict[str, List[str]] = {}

        for lane in self.road_net.get_lanes():
            ret[lane.get_id()] = [vehicle.get_id() for vehicle in lane.get_vehicles()]

        return ret

    def get_vehicle_speed(self) -> Dict[str, float]:
        ret: Dict[str, float] = {}
        for vehicle in self.get_running_vehicles():
            ret[vehicle.get_id()] = vehicle.get_speed()

        return ret

    def get_average_travel_time(self) -> float:
        tt = self.cumulative_travel_time
        n = self.finished_vehicle_cnt
        for key in self.vehicle_pool:
            tt += self.get_current_time() - self.vehicle_pool[key][0].enter_time
            n += 1

        return 0 if n == 0 else tt / n

    def get_vehicle_distance(self) -> Dict[str, float]:
        ret: Dict[str, float] = {}
        for vehicle in self.get_running_vehicles():
            ret[vehicle.get_id()] = vehicle.get_distance()

        return ret

    def set_traffic_light_phase(self, id: str, phaseIndex: int) -> None:
        if self.rlTrafficLight is False:
            print("please set rlTrafficLight to true to enable traffic light control")
            return
        self.road_net.get_intersection_by_id(id).get_traffic_light().set_phase(phaseIndex)

    def set_replay_log_file(self, log_file: str) -> None:
        if not self.saveReplayInConfig:
            print("saveReplay is not set to true in config file!", file=sys.stderr)
            return

        if self.log_out is not None:
            self.log_out.close()

        try:
            self.log_out = open(self.dir + "/" + log_file, 'w')
        except IOError as e:
            print("Failed to open file: ", e, file=sys.stderr)

    def set_save_replay(self, open: bool) -> None:
        if self.saveReplayInConfig is False:
            print("saveReplay is not set to true in config file!", file=sys.stderr)
            return

        self.saveReplay = open

    def reset(self, reset_rnd: bool) -> None:
        for vehicle_pair in self.vehicle_pool.values():
            del vehicle_pair[0]

        for pool in self.thread_vehicle_pool:
            pool.clear()

        self.vehicle_pool.clear()
        self.vehicle_map.clear()
        self.road_net.reset()

        self.finished_vehicle_cnt = 0
        self.cumulative_travel_time = 0

        for flow in self.flows:
            flow.reset()

        self.step = 0
        self.active_vehicle_count = 0
        if reset_rnd:
            np.random.seed(self.seed)

    def set_log_file(self, json_file, log_file):
        try:
            with open(json_file, 'w') as file:
                json.dump(self.json_root, file)
        except IOError:
            print("write roadnet log file error", file=sys.stderr)

        try:
            self.log_out = open(log_file, 'w')
        except IOError as e:
            print("Failed to open log file: ", e, file=sys.stderr)

    def get_running_vehicles(self, include_waiting):
        ret = []
        for vehicle_pair in self.vehicle_pool.values():
            vehicle = vehicle_pair[0]  # Assuming that vehicle object is the first element of vehiclePair object
            if vehicle.is_real() and (include_waiting or vehicle.is_running()):
                ret.append(vehicle)
        return ret

    def schedule_lane_change(self):
        self.lane_change_notify_buffer.sort(key=lambda vehicle: vehicle.lane_change_urgency(), reverse=True)
        for v in self.lane_change_notify_buffer:
            v.update_lane_change_neighbor()
            v.send_signal()
            if v.plan_lane_change() and v.can_change() and not v.is_changing():
                lc = v.get_lane_change()
                if lc.is_gap_valid() and v.get_cur_drivable().is_lane():
                    self.insert_shadow(v)

        self.lane_change_notify_buffer.clear()

    def insert_shadow(self, vehicle):
        thread_index = self.vehicle_pool[vehicle.get_priority()][1]
        shadow: Vehicle = Vehicle(vehicle=vehicle, id=vehicle.get_id() + "_shadow", engine=self)
        self.vehicle_map[shadow.get_id()] = shadow
        self.vehicle_pool[shadow.get_priority()] = (shadow, thread_index)
        self.thread_vehicle_pool[thread_index].append(shadow)
        vehicle.insert_shadow(shadow)
        self.active_vehicle_count += 1

    def loadFromFile(self, file_name: str) -> None:
        pass
        # Archive archive(*this, fileName);
        # archive.resume(*this);

    def set_vehicle_speed(self, vehicle_id: str, speed: float) -> None:
        if vehicle_id not in self.vehicle_map:
            raise Exception("Vehicle '" + vehicle_id + "' not found")
        else:
            self.vehicle_map[vehicle_id].set_custom_speed(speed)

    def get_leader(self, vehicle_id: str) -> str:
        if vehicle_id not in self.vehicle_map:
            raise Exception("Vehicle '" + vehicle_id + "' not found")

        vehicle = self.vehicle_map[vehicle_id]
        if self.laneChange is not None:
            if vehicle.is_real() is False:
                vehicle = vehicle.get_partner()

        leader = vehicle.get_leader()
        if leader is not None:
            return leader.get_id()
        return ""

    def set_route(self, vehicle_id: str, anchor_id: List[str]) -> bool:
        if vehicle_id not in self.vehicle_map:
            return False

        vehicle = self.vehicle_map[vehicle_id]
        anchors: List[Road] = [];

        for road_id in anchor_id:
            anchor = self.road_net.get_road_by_id(road_id)
            if anchor is None:
                return False;
            anchors.append(anchor);

        return vehicle.set_route(anchors)

    def get_vehicle_info(self, vehicle_id: str) -> Dict[str, str]:
        if vehicle_id not in self.vehicle_map:
            raise Exception("Vehicle '" + vehicle_id + "' not found")

        return self.vehicle_map[vehicle_id].get_info()

    def get_current_time(self) -> float:
        return self.step * self.interval

    def rnd(self) -> int:
        return np.random.randint(0, sys.maxsize)

    def get_interval(self) -> float:
        return self.interval
