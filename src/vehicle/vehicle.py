import math
from typing import List

from src.engine.engine import Engine
from src.flow.flow import Flow
from src.roadnet.drivable import Drivable
from src.roadnet.lane import Lane
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road
from src.roadnet.segment import Segment
from src.utility.utility import min2double
from src.vehicle.buffer import Buffer
from src.vehicle.controller_info import ControllerInfo
from src.vehicle.signal import Signal
from src.vehicle.simple_lane_change import SimpleLaneChange
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
            self.buffer: Buffer = vehicle.buffer
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
            self.lane_change: SimpleLaneChange = SimpleLaneChange(self)  # Assuming SimpleLaneChange class exists
            self.flow = flow
            self.controller_info.approaching_intersection_distance = \
                vehicle_info.max_speed ** 2 / vehicle_info.usual_neg_acc / 2 + \
                vehicle_info.max_speed * engine.get_interval() * 2
            while self.engine.check_priority():
                self.priority = self.engine.rnd()
            self.enter_time = self.engine.get_current_time()

            # Default initialization for attributes not set in the constructors
        self.lane_change_info = None  # Init

    def setDeltaDistance(self, dis: float) -> None:
        if self.buffer.isDisSet or dis < self.buffer.deltaDis:
            self.unSetEnd()
            self.unSetDrivable()
            self.buffer.deltaDis = dis
            dis = dis + self.controller_info.dis
            drivable: Drivable = self.getCurDrivable()
            for i in range(drivable.get_length()):
                dis -= drivable.get_length()
                nextDrivable = self.controller_info.router.get_next_drivable(i=i)
                if nextDrivable is None:
                    assert (self.controller_info.router.is_last_road(drivable))
                    self.setEnd(True)

                drivable = nextDrivable
                self.setDrivable(drivable)

            self.setDis(dis)

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

    def get_cur_drivable(self) -> LaneLink | Lane:
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

    def get_partner(self) -> 'Vehicle':
        return self.lane_change_info.partner

    def is_real(self):
        return self.lane_change_info.partnerType != 2

    def set_id(self, new_identifier: str):
        self.id = new_identifier

    def get_id(self):
        return self.id

    def get_target_leader(self) -> 'Vehicle':
        return self.lane_change.target_leader

    def get_no_collision_speed(self, vL: float, dL: float, vF: float, dF: float, gap: float, interval: float,
                               target_gap: float) -> float:
        c: float = vF * interval / 2 + target_gap - 0.5 * vL * vL / dL - gap
        a: float = 0.5 / dF
        b: float = 0.5 * interval
        if b * b < 4 * a * c:
            return -100

        v1: float = 0.5 / a * (math.sqrt(b * b - 4 * a * c) - b)
        v2: float = 2 * vL - dL * interval + 2 * (gap - target_gap) / interval
        return min2double(v1, v2)

    def getMaxNegAcc(self):
        return self.vehicle_info.max_neg_acc

    def receiveSignal(self, sender: 'Vehicle') -> None:
        if self.lane_change.changing:
            return

        signal_recv: Signal = self.lane_change.signal_recv
        signal_send: Signal = self.lane_change.signal_send
        curPriority: int = signal_recv.source.get_priority() if signal_recv else -1
        newPriority: int = sender.get_priority()

        if (signal_recv is None or curPriority < newPriority) and (signal_send is None or self.priority < newPriority):
            self.lane_change.signal_recv = sender.lane_change.signal_send

    def unSetEnd(self):
        self.buffer.isEndSet = False

    def unSetDrivable(self):
        self.buffer.isDrivableSet = False

    def getCurDrivable(self) -> Drivable:
        return self.controller_info.drivable

    def setEnd(self, end: bool) -> None:
        self.buffer.end = end
        self.buffer.isEndSet = True

    def setDrivable(self, drivable: Drivable) -> None:
        self.buffer.drivable = drivable
        self.buffer.isDrivableSet = True

    def setDis(self, dis: float):
        self.buffer.dis = dis
        self.buffer.isDisSet = True
