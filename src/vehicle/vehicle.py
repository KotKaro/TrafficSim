import math
from typing import List, Dict

from src.engine.engine import Engine
from src.flow.flow import Flow
from src.roadnet.lane import Lane
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road
from src.roadnet.segment import Segment
from src.utility.control_info import ControlInfo
from src.utility.utility import min2double, Point, max2double
from src.vehicle.buffer import Buffer
from src.vehicle.controller_info import ControllerInfo
from src.vehicle.lane_change_info import LaneChangeInfo
from src.vehicle.signal import Signal
from src.vehicle.simple_lane_change import SimpleLaneChange
from src.vehicle.vehicle_info import VehicleInfo
from src.roadnet.drivable import Drivable


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

        self.route_valid = False
        self.lane_change_info: LaneChangeInfo = None  # Init

    def set_delta_distance(self, dis: float) -> None:
        if self.buffer.isDisSet or dis < self.buffer.deltaDis:
            self.un_set_end()
            self.un_set_drivable()
            self.buffer.deltaDis = dis
            dis = dis + self.controller_info.dis
            drivable: Drivable = self.get_cur_drivable()
            for i in range(drivable.get_length()):
                dis -= drivable.get_length()
                nextDrivable = self.controller_info.router.get_next_drivable(i=i)
                if nextDrivable is None:
                    assert (self.controller_info.router.is_last_road(drivable))
                    self.set_end(True)

                drivable = nextDrivable
                self.set_drivable(drivable)

            self.set_dis(dis)

    def get_point(self) -> Point:
        if math.fabs(self.lane_change_info.offset) < Point.eps or self.controller_info.drivable.is_lane():
            return self.controller_info.drivable.get_point_by_distance(self.controller_info.dis);
        else:
            assert self.controller_info.drivable.is_lane()
            lane: Lane = self.controller_info.drivable

            origin = lane.get_point_by_distance(self.controller_info.dis)
            next_point: Point
            percentage: float
            lanes = lane.belong_road.get_lanes()

            if self.lane_change_info.offset > 0:
                next_point = lanes[lane.lane_index + 1].get_point_by_distance(self.controller_info.dis)
                percentage = 2 * self.lane_change_info.offset / lane.get_width() + lanes[
                    lane.lane_index + 1].get_width()
            else:
                next_point = lanes[lane.lane_index - 1].get_point_by_distance(self.controller_info.dis)
                percentage = -2 * self.lane_change_info.offset / (
                        lane.get_width() + lanes[lane.lane_index - 1].getWidth())

            return Point(next_point.x * percentage + origin.x * (1 - percentage),
                         next_point.y * percentage + origin.y * (1 - percentage))

    def update(self) -> None:
        if self.buffer.isEndSet:
            self.controller_info.end = self.buffer.end
            self.buffer.isEndSet = False

        if self.buffer.isDisSet:
            self.controller_info.dis = self.buffer.dis
            self.buffer.isDisSet = False

        if self.buffer.isSpeedSet:
            self.vehicle_info.speed = self.buffer.speed
            self.buffer.isSpeedSet = False

        if self.buffer.isCustomSpeedSet:
            self.buffer.isCustomSpeedSet = False

        if self.buffer.isDrivableSet:
            self.controller_info.prevDrivable = self.controller_info.drivable
            self.controller_info.drivable = self.buffer.drivable
            self.buffer.isDrivableSet = False
            self.controller_info.router.update()

        if self.buffer.isEnterLaneLinkTimeSet:
            self.controller_info.enterLaneLinkTime = self.buffer.enterLaneLinkTime
            self.buffer.isEnterLaneLinkTimeSet = False

        if self.buffer.isBlockerSet:
            self.controller_info.blocker = self.buffer.blocker
            self.buffer.isBlockerSet = False
        else:
            self.controller_info.blocker = None

        if self.buffer.isNotifiedVehicles:
            self.buffer.notifiedVehicles.clear()
            self.buffer.isNotifiedVehicles = False

    def get_distance(self) -> float:
        return self.controller_info.dis

    def set_segment_index(self, segment_index: int) -> None:
        self.lane_change_info.segmentIndex = segment_index

    def get_len(self) -> float:
        return self.vehicle_info.len

    def get_speed(self) -> float:
        return self.vehicle_info.speed

    def get_enter_lane_link_time(self) -> float:
        return self.controller_info.enterLaneLinkTime

    def get_priority(self) -> int:
        return self.priority

    def get_blocker(self) -> 'Vehicle':
        return self.controller_info.blocker

    def set_priority(self, priority: int) -> None:
        self.priority = priority

    def get_segment_index(self) -> int:
        return self.lane_change_info.segmentIndex

    def get_offset(self) -> float:
        return self.lane_change_info.offset

    def get_list_iterator(self) -> List['Vehicle']:
        assert self.get_cur_drivable().is_lane()
        seg: Segment = self.get_cur_drivable().get_segment(self.get_segment_index())
        return seg.find_vehicle(self)

    def set_shadow(self, shadow: 'Vehicle') -> None:
        self.lane_change_info.partnerType = 1
        self.lane_change_info.partner = shadow

    def set_parent(self, vehicle: 'Vehicle'):
        self.lane_change_info.partnerType = 2
        self.lane_change_info.partner = vehicle

    def update_leader_and_gap(self, leader: 'Vehicle') -> None:
        if leader is not None and leader.get_cur_drivable() == self.get_cur_drivable():
            self.controller_info.leader = leader
            self.controller_info.gap = leader.get_distance() - leader.get_len() - self.controller_info.dis
        else:
            self.controller_info.leader = None
            dis = self.controller_info.drivable.get_length() - self.controller_info.dis
            i = 0
            while True:
                i += 1
                drivable = self.get_next_drivable(i)
                if drivable is None:
                    return

                if drivable.is_lane_link():
                    for lane_link in drivable.get_start_lane().lane_links:
                        candidateLeader = lane_link.get_last_vehicle()
                        if candidateLeader is not None:
                            candidateGap = dis + candidateLeader.get_distance() - candidateLeader.get_len()
                            if self.controller_info.leader is None or candidateGap < self.controller_info.gap:
                                self.controller_info.leader = candidateLeader;
                                self.controller_info.gap = candidateGap;
                    if self.controller_info.leader:
                        return
                else:
                    self.controller_info.leader = drivable.get_last_vehicle()
                    if self.controller_info.leader is not None:
                        self.controller_info.gap = (dis + self.controller_info.leader.get_distance()
                                                    - self.controller_info.leader.get_len())
                        return

                dis += drivable.get_length()
                if (dis > self.vehicle_info.max_speed
                        * self.vehicle_info.max_speed
                        / self.vehicle_info.usual_neg_acc
                        / 2
                        + self.vehicle_info.max_speed
                        * self.engine.get_interval() * 2):
                    return

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

    @staticmethod
    def get_no_collision_speed(vL: float, dL: float, vF: float, dF: float, gap: float, interval: float,
                               target_gap: float) -> float:
        c: float = vF * interval / 2 + target_gap - 0.5 * vL * vL / dL - gap
        a: float = 0.5 / dF
        b: float = 0.5 * interval
        if b * b < 4 * a * c:
            return -100

        v1: float = 0.5 / a * (math.sqrt(b * b - 4 * a * c) - b)
        v2: float = 2 * vL - dL * interval + 2 * (gap - target_gap) / interval
        return min2double(v1, v2)

    def get_car_follow_speed(self, interval: float) -> float:
        leader = self.get_leader()
        if leader is None:
            return self.buffer.customSpeed if self.hasSetCustomSpeed() else self.vehicle_info.max_speed

        v = self.get_no_collision_speed(leader.get_speed(), leader.get_max_neg_acc(), self.vehicle_info.speed,
                                        self.vehicle_info.max_neg_acc, self.controller_info.gap, interval, 0)

        if self.hasSetCustomSpeed():
            return min2double(self.buffer.customSpeed, v)

        assume_decel = 0.0
        leaderSpeed = leader.get_speed()
        if self.vehicle_info.speed > leaderSpeed:
            assume_decel = self.vehicle_info.speed - leaderSpeed

        v = min2double(v,
                       self.get_no_collision_speed(leader.get_speed(), leader.getUsualNegAcc(), self.vehicle_info.speed,
                                                   self.vehicle_info.usual_neg_acc, self.controller_info.gap, interval,
                                                   self.vehicle_info.min_gap))
        v = min2double(v,
                       (self.controller_info.gap + (leaderSpeed + assume_decel / 2) * interval -
                        self.vehicle_info.speed * interval / 2) / (self.vehicle_info.headway_time + interval / 2))

        return v

    def get_stop_before_speed(self, distance: float, interval: float) -> float:
        assert (distance >= 0);
        if self.get_brake_distance_after_accel(
                self.vehicle_info.usual_pos_acc,
                self.vehicle_info.usual_neg_acc, interval) < distance:
            return self.vehicle_info.speed + self.vehicle_info.usual_pos_acc * interval

        take_interval = 2 * distance / (self.vehicle_info.speed.speed + Point.eps) / interval
        if take_interval >= 1:
            return self.vehicle_info.speed - self.vehicle_info.speed / take_interval

        return self.vehicle_info.speed - self.vehicle_info.speed / take_interval

    def get_reach_steps(self, distance: float, target_speed: float, acc: float) -> int:
        if distance <= 0:
            return 0

        if self.vehicle_info.speed > target_speed:
            return math.ceil(distance / self.vehicle_info.speed)

        distance_until_target_speed = self.get_distance_until_speed(target_speed, acc)
        interval = self.engine.get_interval()
        if distance_until_target_speed > distance:
            return math.ceil((math.sqrt(
                self.vehicle_info.speed * self.vehicle_info.speed + 2 * acc * distance) - self.vehicle_info.speed) / acc / interval)
        else:
            return math.ceil((target_speed - self.vehicle_info.speed) / acc / interval) + math.ceil(
                (distance - distance_until_target_speed) / target_speed / interval)

    def get_reach_steps_on_lane_link(self, distance: float, lane_link: LaneLink) -> int:
        return self.get_reach_steps(distance,
                                    self.vehicle_info.turn_speed if lane_link.is_turn() else self.vehicle_info.max_speed,
                                    self.vehicle_info.usual_pos_acc)

    def get_distance_until_speed(self, speed: float, acc: float) -> float:
        if speed <= self.vehicle_info.speed:
            return 0

        interval = self.engine.get_interval()
        stage1steps = math.floor((speed - self.vehicle_info.speed) / acc / interval)
        stage1speed = self.vehicle_info.speed + stage1steps * acc / interval
        stage1dis = (self.vehicle_info.speed + stage1speed) * (stage1steps * interval) / 2

        return stage1dis + (stage1speed + speed) * interval / 2 if stage1speed < speed else 0

    def can_yield(self, dist: float) -> bool:
        return (dist > 0 and self.get_min_brake_distance() < dist - self.vehicle_info.yield_distance) or (
                dist < 0 and dist + self.vehicle_info.len < 0)

    def is_intersection_related(self) -> bool:
        if self.controller_info.drivable.is_lane_link():
            return True
        if self.controller_info.drivable.is_lane():
            drivable = self.get_next_drivable()
            if (
                    drivable and drivable.is_lane_link() and self.controller_info.drivable.get_length() - self.controller_info.dis <=
                    self.controller_info.approachingIntersectionDistance):
                return True

        return False

    def get_next_speed(self, interval: float) -> ControlInfo:
        drivable = self.controller_info.drivable
        v = self.vehicle_info.max_speed
        v = min2double(v, self.vehicle_info.speed + self.vehicle_info.max_pos_acc * interval)
        v = min2double(v, drivable.get_max_speed())
        v = min2double(v, self.get_car_follow_speed(interval))

        if self.is_intersection_related():
            v = min2double(v, self.get_intersection_related_speed(interval))

        if self.lane_change:
            v = min2double(v, self.lane_change.yield_speed(interval))
            if self.controller_info.router.on_valid_lane() is False:
                vn = self.get_no_collision_speed(0, 1, self.get_speed(), self.get_max_neg_acc(),
                                                 self.get_cur_drivable().get_length() - self.get_distance(), interval,
                                                 self.get_min_gap())
                v = min2double(v, vn)

        v = max2double(v, self.vehicle_info.speed - self.vehicle_info.max_neg_acc * interval)
        return ControlInfo(speed=v)

    def get_intersection_related_speed(self, interval: float) -> float:
        v = self.vehicle_info.max_speed
        next_drivable = self.get_next_drivable()
        # const LaneLink *laneLink = nullptr;
        if next_drivable and next_drivable.is_lane_link():
            laneLink: LaneLink = next_drivable
            if laneLink.is_available() is False or laneLink.get_end_lane().can_enter(self) is False:
                if self.get_min_brake_distance() > self.controller_info.drivable.get_length() - self.controller_info.dis:
                    # TODO: what if it cannot brake before red light?
                    print('')
                else:
                    v = min2double(v, self.get_stop_before_speed(
                        self.controller_info.drivable.get_length() - self.controller_info.dis, interval))
                    return v
            if laneLink.is_turn():
                v = min2double(v, self.vehicle_info.turn_speed)  # TODO define turn speed

        if laneLink is None and self.controller_info.drivable.is_lane_link():
            laneLink: LaneLink = self.controller_info.drivable

        self.controller_info.drivable.get_length()
        distanceToLaneLinkStart = -(self.controller_info.drivable.get_length() - self.controller_info.dis) \
            if self.controller_info.drivable.is_lane() \
            else self.controller_info.dis

        for cross in laneLink.get_crosses():
            distanceOnLaneLink = cross.get_safe_distance_by_lane(laneLink)
            if distanceOnLaneLink < distanceToLaneLinkStart:
                continue

            if cross.can_pass(self, laneLink, distanceToLaneLinkStart):
                v = min2double(v, self.get_stop_before_speed(
                    distanceOnLaneLink - distanceToLaneLinkStart - self.vehicle_info.yield_distance, interval))
                self.set_blocker(cross.get_foe_vehicle(laneLink))
                break

        return v

    def get_max_neg_acc(self):
        return self.vehicle_info.max_neg_acc

    def receive_signal(self, sender: 'Vehicle') -> None:
        if self.lane_change.changing:
            return

        signal_recv: Signal = self.lane_change.signal_recv
        signal_send: Signal = self.lane_change.signal_send
        curPriority: int = signal_recv.source.get_priority() if signal_recv else -1
        newPriority: int = sender.get_priority()

        if (signal_recv is None or curPriority < newPriority) and (signal_send is None or self.priority < newPriority):
            self.lane_change.signal_recv = sender.lane_change.signal_send

    def un_set_end(self):
        self.buffer.isEndSet = False

    def un_set_drivable(self):
        self.buffer.isDrivableSet = False

    def get_cur_drivable(self) -> Drivable:
        return self.controller_info.drivable

    def set_end(self, end: bool) -> None:
        self.buffer.end = end
        self.buffer.isEndSet = True

    def set_drivable(self, drivable: Drivable) -> None:
        self.buffer.drivable = drivable
        self.buffer.isDrivableSet = True

    def set_dis(self, dis: float):
        self.buffer.dis = dis
        self.buffer.isDisSet = True

    def set_speed(self, speed: float) -> None:
        self.buffer.speed = speed
        self.buffer.isSpeedSet = True

    def get_changed_drivable(self) -> Drivable | None:
        if self.buffer.isDrivableSet is False:
            return None
        return self.buffer.drivable

    def get_next_drivable(self, i=0) -> Drivable:
        return self.controller_info.router.get_next_drivable(i=i)

    def get_leader(self) -> 'Vehicle':
        return self.controller_info.leader

    def hasSetCustomSpeed(self) -> bool:
        return self.buffer.isCustomSpeedSet

    def getUsualNegAcc(self):
        return self.vehicle_info.usual_neg_acc

    def get_brake_distance_after_accel(self, acc: float, dec: float, interval: float) -> float:
        current_speed = self.vehicle_info.speed
        next_speed = current_speed + acc * interval
        return (current_speed + next_speed) * interval / 2 + (next_speed * next_speed / dec / 2)

    def get_min_brake_distance(self) -> float:
        return 0.5 * self.vehicle_info.speed * self.vehicle_info.speed / self.vehicle_info.max_neg_acc

    def set_blocker(self, blocker: 'Vehicle') -> None:
        self.buffer.blocker = blocker
        self.buffer.isBlockerSet = True

    def get_min_gap(self) -> float:
        return self.vehicle_info.min_gap

    def finish_changing(self) -> None:
        self.lane_change.finish_changing()
        self.set_end(True)

    def abort_lane_change(self) -> None:
        assert self.lane_change_info.partner is not None
        self.set_end(True)
        self.lane_change.abort_changing()

    def get_first_road(self) -> Road:
        return self.controller_info.router.get_first_road()

    def set_first_drivable(self) -> None:
        self.controller_info.drivable = self.controller_info.router.get_first_drivable()

    def update_route(self) -> None:
        self.route_valid = self.controller_info.router.update_shortest_path()

    def set_route(self, anchor: List[Road]) -> bool:
        return self.controller_info.router.set_route(anchor)

    def get_info(self) -> Dict[str, str]:
        info = {
            "running": str(self.is_running())
        }

        if self.is_running() is False:
            return info

        drivable = self.get_cur_drivable()
        road = self.get_cur_drivable().belong_road if drivable.is_lane() else None
        return {
            **info,
            "distance": str(self.get_distance()),
            "speed": str(self.get_speed()),
            "drivable": drivable.get_id(),
            **({
                   "road": road.get_id(),
                   "intersection": road.get_end_intersection().get_id()
               } if drivable.is_lane() else {}),
            "route": " ".join([r.get_id() for r in self.controller_info.router.get_following_roads()])
        }

    def is_running(self) -> bool:
        return self.controller_info.running
