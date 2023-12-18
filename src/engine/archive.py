from collections import deque
from typing import Dict, Tuple, List, Deque

from src.engine.engine import Engine
from src.flow.flow import Flow
from src.roadnet.drivable import Drivable
from src.roadnet.history_record import HistoryRecord
from src.roadnet.intersection import Intersection
from src.vehicle.vehicle import Vehicle


class DrivableArchive:
    def __init__(self):
        self.vehicles: List[Vehicle] = []
        self.waiting_buffer: Deque[Vehicle] = deque()
        self.history: List[HistoryRecord] = []
        self.history_average_speed: float = 0
        self.history_vehicle_num: int = 0


class FlowArchive:
    def __init__(self, now_time: float, current_time: float, cnt: int):
        self.now_time: float = now_time
        self.current_time: float = current_time
        self.cnt: int = cnt


class TrafficLightArchive:
    def __init__(self, remain_duration: float, cur_phase_index: int):
        self.remain_duration: float = remain_duration
        self.cur_phase_index: int = cur_phase_index


class Archive:

    def __init__(self, engine: Engine):
        self.step: int = engine.step
        self.active_vehicle_count: int = engine.active_vehicle_count
        self.finished_vehicle_cnt = engine.finished_vehicle_cnt
        self.cumulative_travel_time = engine.cumulative_travel_time
        self.vehicle_pool: Dict[int, Tuple[Vehicle, int]] = engine.vehicle_pool.copy()
        self.drivable_archive: Dict[Drivable, DrivableArchive] = {}
        self.flows_archive: Dict[Flow, FlowArchive] = {}
        self.traffic_lights_archive: Dict[Intersection, TrafficLightArchive] = {}

        for drivable in engine.road_net.get_drivables():
            archive = DrivableArchive()
            self.drivable_archive[drivable] = archive
            self.archive_drivable(drivable, archive)

        for flow in engine.flows:
            self.flows_archive[flow] = FlowArchive(flow.now_time, flow.current_time, flow.cnt)

        for intersection in engine.road_net.get_intersections():
            light = intersection.get_traffic_light()
            self.traffic_lights_archive[intersection] = TrafficLightArchive(light.remain_duration,
                                                                            light.cur_phase_index)

    def archive_drivable(self, drivable: Drivable, drivable_archive: DrivableArchive) -> None:
        for vehicle in drivable.get_vehicles():
            drivable_archive.vehicles.append(self.getNewPointer(self.vehicle_pool, vehicle))

        if drivable.is_lane():
            for vehicle in drivable.get_waiting_buffer():
                drivable_archive.waiting_buffer.append(self.getNewPointer(self.vehicle_pool, vehicle))

            drivable_archive.history = drivable.history
            drivable_archive.historyVehicleNum = drivable.historyVehicleNum
            drivable_archive.historyAverageSpeed = drivable.historyAverageSpeed

    def getNewPointer(self, vehicle_pool: Dict[int, Tuple[Vehicle, int]], old: Vehicle) -> Vehicle | None:
        if old is None:
            return None

        priority = old.get_priority()
        assert priority in vehicle_pool
        return vehicle_pool[priority][0]

    def resume(self, engine: Engine) -> None:
        engine.step = self.step
        engine.active_vehicle_count = self.active_vehicle_count

        for key in list(engine.vehicle_pool.keys()):
            del engine.vehicle_pool[key]

        engine.vehiclePool = self.copy_vehicle_pool(self.vehicle_pool)
        engine.vehicle_map.clear()

        for key in list(engine.vehicle_pool.keys()):
            vehicle = engine.vehicle_pool[key][0]
            engine.vehicle_map[vehicle.get_id()] = vehicle

        for thread_veh in engine.thread_vehicle_pool:
            thread_veh.clear()

        for pair in list(engine.vehicle_pool.keys()):
            vehicle = engine.vehicle_pool[pair][0]
            thread_index = engine.vehicle_pool[pair][1]
            engine.thread_vehicle_pool[thread_index].append(vehicle)

        for drivable in engine.road_net.get_drivables():
            archive = self.drivable_archive[drivable]
            drivable.vehicles.clear()

            for vehicle in archive.vehicles:
                drivable.vehicles.append(self.getNewPointer(engine.vehicle_pool, vehicle))

            if drivable.is_lane():
                drivable.waiting_buffer.clear()

                for vehicle in archive.waiting_buffer:
                    drivable.waiting_buffer.append(self.getNewPointer(engine.vehicle_pool, vehicle))

                drivable.history = archive.history
                drivable.historyVehicleNum = archive.history_vehicle_num
                drivable.historyAverageSpeed = archive.history_average_speed

        for flow in engine.flows:
            archive = self.flows_archive[flow]
            flow.current_time = archive.current_time
            flow.now_time = archive.now_time
            flow.cnt = archive.cnt

        for intersection in engine.road_net.get_intersections():
            light = intersection.get_traffic_light()
            archive = self.traffic_lights_archive[intersection]
            light.remainDuration = archive.remain_duration
            light.curPhaseIndex = archive.cur_phase_index

        engine.finished_vehicle_cnt = self.finished_vehicle_cnt
        engine.cumulative_travel_time = self.cumulative_travel_time

    def copy_vehicle_pool(self, src: Dict[int, Tuple[Vehicle, int]]) -> Dict[int, Tuple[Vehicle, int]]:
        new_pool: Dict[int, Tuple[Vehicle, int]] = {}
        for key in src.items():
            old_vehicle = key[1][0]
            new_vehicle = Vehicle(vehicle=old_vehicle)
            new_pool[old_vehicle.get_priority()] = (new_vehicle, key[1][1])

        for veh in new_pool.items():
            vehicle = veh[1][0]
            vehicle.lane_change_info.partner = self.getNewPointer(new_pool, vehicle.lane_change_info.partner)
            vehicle.controller_info.leader = self.getNewPointer(new_pool, vehicle.controller_info.leader)
            vehicle.controller_info.blocker = self.getNewPointer(new_pool, vehicle.controller_info.blocker)

            lane_change = vehicle.lane_change
            lane_change.target_leader = self.getNewPointer(new_pool, lane_change.target_leader)
            lane_change, targetFollower = self.getNewPointer(new_pool, lane_change.target_follower)
            if lane_change.signal_recv:
                lane_change.signal_recv = self.getNewPointer(new_pool,
                                                             lane_change.signal_recv.source).lane_change.signal_send

        return new_pool
