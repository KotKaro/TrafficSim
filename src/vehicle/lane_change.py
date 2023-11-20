import sys
from copy import copy

from src.vehicle.signal import Signal
from src.vehicle.vehicle import Vehicle
from src.roadnet.lane import Lane


class LaneChange:
    cooling_time = 3  # Static member equivalent

    def __init__(self, vehicle: Vehicle, other: 'LaneChange' = None):
        self.vehicle: Vehicle = vehicle
        self.last_dir: int = None if other is None else other.last_dir
        self.signal_recv: Signal = None if other is None else other.signal_recv

        if other is not None:
            copy_signal: Signal = copy(other.signal_send)
            copy_signal.source = vehicle
        else:
            copy_signal: Signal = None
        self.signal_send: Signal = copy_signal

        self.target_leader: Vehicle = None if other is None else other.target_leader
        self.target_follower: Vehicle = None if other is None else other.target_follower
        self.leader_gap: float = 0 if other is None else other.leader_gap
        self.follower_gap: float = 0 if other is None else other.follower_gap
        self.waiting_time: float = 0 if other is None else other.waiting_time
        self.changing: bool = False if other is None else other.changing
        self.finished: bool = False if other is None else other.finished
        self.last_change_time: float = 0 if other is None else other.last_change_time

    def update_leader_and_follower(self) -> None:
        self.target_follower = None
        self.target_leader = None
        target: Lane = self.signal_send.target
        self.target_leader: Vehicle = target.get_vehicle_after_distance(self.vehicle.get_distance(),
                                                                        self.vehicle.get_segment_index())
        curLane: Lane = self.vehicle.get_cur_drivable()

        self.leader_gap = sys.float_info.max
        self.follower_gap = sys.float_info.max

        if self.target_leader is None:
            rest: float = curLane.get_length() - self.vehicle.get_distance()
            self.leader_gap = rest
            gap = sys.float_info.max
            for lane_link in self.signal_send.target.lane_links:
                leader = lane_link.get_last_vehicle()
                if leader and leader.get_distance() + rest < gap:
                    gap = leader.get_distance() + rest
                    if gap < leader.get_len():
                        self.target_leader = leader
                        self.leader_gap = rest - (leader.get_len() - gap)
        else:
            self.leader_gap = (self.target_leader.get_distance()
                               - self.vehicle.get_distance()
                               - self.target_leader.get_len())

        targetFollower = target.get_vehicle_before_distance(self.vehicle.get_distance(),
                                                            self.vehicle.get_segment_index())
        # TODO : potential bug here: a vehicle entering the lane is too close.
        self.follower_gap = self.vehicle.get_distance() - targetFollower.get_distance() - self.vehicle.get_len() \
            if targetFollower \
            else sys.float_info.max

    def get_target(self) -> Lane:
        assert self.vehicle.get_cur_drivable().is_lane()
        return self.signal_send.target if self.signal_send else self.vehicle.get_cur_drivable()

    def gap_before(self) -> float:
        return self.follower_gap

    def gap_after(self) -> float:
        return self.leader_gap

    def insert_shadow(self, shadow: Vehicle):
        assert self.changing is False
        assert self.vehicle.get_offset() == 0

        self.changing = True
        self.waiting_time = 0

        assert self.vehicle.get_cur_drivable().is_lane()
        targetLane: Lane = self.signal_send.target
        segId: int = self.vehicle.get_segment_index()
        targetSeg = targetLane.get_segment(segId)

        shadow.set_parent(self.vehicle)
        self.vehicle.set_shadow(shadow)

        shadow.controllerInfo.blocker = None
        shadow.controllerInfo.drivable = targetLane
        shadow.controllerInfo.router.update()

        targetFollowerItr = [vehicle for vehicle in (self.target_follower.getListIterator() if self.target_follower else targetLane.get_vehicles())]
        targetLane.get_vehicles().insert(targetFollowerItr, shadow)
        targetSeg.insert_vehicle(targetLane.get_vehicles())

        shadow.update_leader_and_gap(self.target_leader)
        if self.target_follower:
            self.target_follower.update_leader_and_gap(shadow)

    def safe_gap_before(self) -> float:
        raise NotImplementedError

    def safe_gap_after(self) -> float:
        raise NotImplementedError

    def plan_change(self) -> bool:
        return ((self.signal_send
                 and self.signal_send.target
                 and self.signal_send.target != self.vehicle.get_cur_drivable())
                or self.changing)

    def can_change(self) -> bool:
        return self.signal_send and not self.signal_recv

    def is_gap_valid(self) -> bool:
        return self.gap_after() >= self.safe_gap_after() and self.gap_before() >= self.safe_gap_before()

    def finish_changing(self) -> None:
        self.changing = False
        self.finished = True
        self.last_change_time = self.vehicle.engine.get_current_time()
        partner = self.vehicle.get_partner()
        if partner.is_real():
            partner.set_id(self.vehicle.get_id())

        partner.lane_change_info.partnerType = 0
        partner.lane_change_info.offset = 0
        partner.lane_change_info.partner = None
        self.vehicle.lane_change_info.partner = None
        self.clear_signal()

    def abort_changing(self) -> None:
        partner = self.vehicle.get_partner()
        partner.lane_change.changing = False
        partner.lane_change.partnerType = 0
        partner.lane_change.offset = 0
        partner.lane_change.partner = None
        self.clear_signal()

    def yield_speed(self, interval):
        raise NotImplementedError

    def send_signal(self):
        raise NotImplementedError

    def get_direction(self) -> int:
        if self.vehicle.get_cur_drivable().is_lane():
            return 0

        curLane: Lane = self.vehicle.get_cur_drivable()
        if self.signal_send is None:
            return 0

        if self.signal_send.target is None:
            return 0

        if self.signal_send.target == curLane.get_outer_lane():
            return 1

        if self.signal_send.target == curLane.get_inner_lane():
            return -1

        return 0

    def clear_signal(self):
        self.target_leader = None
        self.target_follower = None
        if self.signal_send is not None:
            self.last_dir = self.signal_send.direction
        else:
            self.last_dir = 0
        if self.changing:
            return
        self.signal_send = None
        self.signal_recv = None

    def has_finished(self):
        return self.finished
