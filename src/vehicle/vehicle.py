from typing import List

from src.engine.engine import Engine
from src.flow.flow import Flow
from src.roadnet.drivable import Drivable
from src.roadnet.road import Road
from src.roadnet.segment import Segment
from src.vehicle.controller_info import ControllerInfo
from src.vehicle.vehicle_info import VehicleInfo


class Vehicle:

    def __init__(self, vehicle: 'Vehicle' = None,
                 vehicle_info: VehicleInfo = None,
                 id: str = None,
                 engine: Engine = None,
                 flow: Flow = None):
        self.controllerInfo: ControllerInfo = None
        if vehicle is not None and vehicle_info is None:
            # Acting as the copy constructor
            self.vehicle_info = vehicle.vehicle_info
            self.controller_info = ControllerInfo(self, other=vehicle.controller_info)
            self.lane_change_info = vehicle.lane_change_info
            self.buffer = vehicle.buffer
            self.priority = vehicle.priority
            self.id = vehicle.id if id is None else id
            self.engine: Engine = vehicle.engine if engine is None else engine
            self.lane_change = SimpleLaneChange(self, vehicle.lane_change)  # Assuming SimpleLaneChange class exists
            self.flow = flow
            self.enter_time = vehicle.enter_time

            if id is not None:
                while self.engine.check_priority():
                    self.priority = self.engine.rnd()  # Assuming rnd method in engine returns a random number
                self.controller_info.router.set_vehicle(self)

        elif vehicle_info is not None:
            # Acting as the constructor with VehicleInfo
            self.vehicle_info = vehicle_info
            self.controller_info: ControllerInfo = ControllerInfo(self, route=vehicle_info.route, rnd=engine.rnd)
            self.id = id
            self.engine: Engine = engine
            self.lane_change = SimpleLaneChange(self)  # Assuming SimpleLaneChange class exists
            self.flow = flow
            self.controller_info.approaching_intersection_distance = \
                vehicle_info.max_speed ** 2 / vehicle_info.usual_neg_acc / 2 + \
                vehicle_info.max_speed * engine.get_interval() * 2
            while self.engine.check_priority():
                self.priority = self.engine.rnd()
            self.enter_time = self.engine.get_current_time()

            # Default initialization for attributes not set in the constructors
        self.lane_change_info = None  # Initi

    def get_distance(self) -> float:
        pass

    def set_segment_index(self, index: int):
        pass

    def get_len(self) -> float:
        return self.vehicle_info.len

    def get_speed(self):
        pass

    def get_reach_steps_on_lane_link(self, d2, param):
        pass

    def get_enter_lane_link_time(self):
        pass

    def get_priority(self) -> int:
        pass

    def get_blocker(self):
        pass

    def can_yield(self, d1):
        pass

    def setPriority(self, priority: int):
        pass

    def get_first_road(self) -> Road:
        pass

    def get_segment_index(self) -> int:
        pass

    def get_cur_drivable(self) -> Drivable:
        pass

    def get_offset(self) -> float:
        return self.lane_change_info.offset

    def getListIterator(self) -> List['Vehicle']:
        assert self.get_cur_drivable().is_lane()
        seg: Segment = self.get_cur_drivable().get_segment(self.get_segment_index())
        return seg.find_vehicle(self)

    def set_shadow(self, shadow):
        pass

    def set_parent(self, vehicle):
        pass

    def update_leader_and_gap(self, target_leader):
        pass

    def get_gap(self) -> float:
        return self.controllerInfo.gap

    def get_max_speed(self) -> float:
        return self.vehicle_info.max_speed
