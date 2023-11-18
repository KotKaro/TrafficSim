from collections import deque
from typing import List

from src.roadnet.drivable import Drivable, DrivableType
from src.roadnet.history_record import HistoryRecord
from src.roadnet.lane_link import LaneLink
from src.roadnet.road import Road
from src.roadnet.segment import Segment
from src.vehicle.vehicle import Vehicle


class Lane(Drivable):
    history_len = 240

    def __init__(self, width: float = 0, max_speed: float = 0, lane_index: int = -1, belong_road: Road = None):
        self.width: float = width
        self.max_speed: float = max_speed
        self.lane_index = lane_index
        self.segments: List[Segment] = []
        self.lane_links: List[LaneLink] = []
        self.belong_road: Road = belong_road
        self.waiting_buffer = deque()
        self.history: List[HistoryRecord] = []
        self.drivable_type = DrivableType.LANE

        self.historyVehicleNum = 0
        self.historyAverageSpeed = 0

    def get_id(self):
        return self.belong_road.get_id() + '_' + str(self.lane_index)

    def available(self, vehicle) -> bool:
        if len(self.vehicles) > 0:
            tail = self.vehicles[-1]
            return tail.get_distance() > tail.get_len() + vehicle.get_min_gap()
        else:
            return True

    def can_enter(self, vehicle: Vehicle):
        if len(self.vehicles):
            tail = self.vehicles[-1]
            return tail.get_distance() > tail.get_len() + vehicle.get_len() or tail.get_speed() >= 2
        else:
            return True

    def get_inner_lane(self):
        return self.belong_road.lanes[self.lane_index - 1] if self.lane_index > 0 else None

    def get_outer_lane(self):
        lane_num = len(self.belong_road.lanes)
        if self.lane_index < lane_num - 1:
            return self.belong_road.lanes[self.lane_index + 1]
        else:
            return None

    def get_start_intersection(self):
        return self.belong_road.start_intersection

    def get_end_intersection(self):
        return self.belong_road.end_intersection

    def get_lane_links_to_road(self, road) -> List[LaneLink]:
        return [lane_link for lane_link in self.lane_links if lane_link.get_end_lane() == road]

    def reset(self):
        self.waiting_buffer.clear()
        self.vehicles.clear()

    def get_waiting_buffer(self):
        return self.waiting_buffer

    def push_waiting_vehicle(self, vehicle):
        self.waiting_buffer.append(vehicle)

    def build_segmentation(self, number_of_segments) -> None:
        self.segments = [
            Segment(index, self, index * self.length / number_of_segments,
                    (index + 1) * self.length / number_of_segments)
            for index
            in range(number_of_segments)
        ]

    def initSegments(self):
        iter_index = 0
        for i in range(len(self.segments) - 1):
            seg = self.segments[i]
            seg.vehicles.clear()

            while iter_index < len(self.vehicles) and self.vehicles[iter_index].get_distance() >= seg.get_start_pos():
                seg.vehicles.append(self.vehicles[iter_index])
                self.vehicles[iter_index].set_segment_index(seg.index)
                iter_index += 1

    def get_segment(self, index) -> Segment:
        return self.segments[index]

    def get_segments(self):
        return self.segments

    def get_segment_num(self):
        return len(self.segments)

    def get_vehicles_before_distance(self, dis, segment_index: int) -> Vehicle | None:
        for i in reversed(range(segment_index)):
            vehicles = self.get_segment(i).get_vehicles()
            for vehicle in vehicles:
                if vehicle.get_distance() < dis:
                    return vehicle

        return None

    def update_history(self) -> None:
        speed_sum = self.historyVehicleNum * self.historyAverageSpeed

        while len(self.history) > self.history_len:
            self.historyVehicleNum -= self.history[0].vehicle_num
            speed_sum -= self.history[0].vehicle_num * self.history[0].average_speed
            self.history.pop(0)  # Removes the first element

        cur_speed_sum = 0
        vehicle_num = len(self.get_vehicles())
        self.historyVehicleNum += vehicle_num

        for vehicle in self.get_vehicles():
            cur_speed_sum += vehicle.get_speed()

        speed_sum += cur_speed_sum
        if vehicle_num != 0:
            self.history.append(HistoryRecord(vehicle_num, cur_speed_sum / vehicle_num))
        else:
            self.history.append(HistoryRecord(vehicle_num, 0))

        if self.historyVehicleNum != 0:
            self.historyAverageSpeed = speed_sum / self.historyVehicleNum
        else:
            self.historyAverageSpeed = 0

    def get_vehicle_before_distance(self, dis: float, segment_index: int) -> Vehicle | None:
        for i in reversed(range(segment_index)):
            for vehicle in self.get_segment(i).get_vehicles():
                if vehicle.get_distance() < dis:
                    return vehicle

        return None

    def get_vehicle_after_distance(self, dis, segment_index: int) -> Vehicle | None:
        for i in range(segment_index, self.get_segment_num()):
            for vehicle in self.get_segment(i).get_vehicles():
                if vehicle.get_distance() >= dis:
                    return vehicle

        return None
