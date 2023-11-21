from src.roadnet.lane import Lane
from src.vehicle.lane_change import LaneChange
from src.vehicle.router import Router
from src.vehicle.signal import Signal
from src.vehicle.vehicle import Vehicle


class SimpleLaneChange(LaneChange):
    def make_signal(self, interval):
        if self.changing: return;
        if self.vehicle.engine.get_current_time() - self.last_change_time < self.cooling_time:
            return
        self.signal_send = Signal()
        self.signal_send.source = self.vehicle

        if self.vehicle.get_cur_drivable().is_lane():
            curLane: Lane = self.vehicle.get_cur_drivable()
            if curLane.get_length() - self.vehicle.get_distance() < 30:
                return

            curEst: float = self.vehicle.get_gap()
            outerEst: float = 0
            expectedGap: float = 2 * self.vehicle.get_len() + 4 * interval * self.vehicle.get_max_speed()
            if self.vehicle.get_gap() > expectedGap or self.vehicle.get_gap() < 1.5 * self.vehicle.get_len():
                return

            router: Router = self.vehicle.controller_info.router
            if curLane.lane_index < len(curLane.belong_road.get_lanes()) - 1:
                if router.on_last_road() or router.get_next_drivable(curr_drivable=curLane.get_outer_lane()):
                    outerEst = self.estimate_gap(curLane.get_outer_lane())
                    if outerEst > curEst + self.vehicle.get_len():
                        self.signal_send.target = curLane.get_outer_lane()

            if curLane.lane_index > 0:
                if router.on_last_road() or router.get_next_drivable(curr_drivable=curLane.get_inner_lane()):
                    innerEst = self.estimate_gap(curLane.get_inner_lane())
                    if innerEst > curEst + self.vehicle.get_len() and innerEst > outerEst:
                        self.signal_send.target = curLane.get_inner_lane()

            self.signal_send.urgency = 1

        self.make_signal(interval)

    def estimate_gap(self, lane: Lane) -> float:
        curSegIndex: int = self.vehicle.get_segment_index()
        leader: Vehicle = lane.get_vehicle_after_distance(self.vehicle.get_distance(), curSegIndex)
        if leader is None:
            return lane.get_length() - self.vehicle.get_distance()
        else:
            return leader.get_distance() - self.vehicle.get_distance() - leader.get_len()

    def yield_speed(self, interval: float) -> float:
        if self.plan_change():
            self.waiting_time += interval

        if self.signal_recv:
            if self.vehicle == self.signal_recv.source.get_target_leader():
                return 100
            else:
                source: Vehicle = self.signal_recv.source
                srcSpeed: float = source.get_speed()
                gap: float = source.lane_change.gap_before() - source.lane_change.safe_gap_before()

                v = self.vehicle.getNoCollisionSpeed(srcSpeed, source.getMaxNegAcc(),
                                                     self.vehicle.get_speed(),
                                                     self.vehicle.getMaxNegAcc(),
                                                     gap, interval,
                                                     0)

                if v < 0:
                    v = 100
                # If the follower is too fast, let it go.

                return v
        return 100

    def send_signal(self) -> None:
        if (self.target_leader):
            self.target_leader.receiveSignal(self.vehicle)

        if self.target_follower:
            self.target_follower.receiveSignal(self.vehicle)

    def safe_gap_before(self) -> float:
        return self.target_follower.getMinBrakeDistance() if self.target_follower is not None else 0

    def safe_gap_after(self) -> float:
        return self.vehicle.getMinBrakeDistance()
