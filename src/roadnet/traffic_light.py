from typing import List

from src.roadnet.intersection import Intersection


class LightPhase:
    def __init__(self):
        self.phase = 0
        self.time = 0.0
        self.road_link_available = []


class TrafficLight:
    def __init__(self):
        self.intersection: Intersection = None
        self.phases: List[LightPhase] = []
        self.road_link_indices: List[int] = []
        self.remain_duration = 0.0
        self.cur_phase_index = 0

    def init(self, init_phase_index):
        if self.intersection and not self.intersection.is_virtual:
            self.cur_phase_index = init_phase_index
            self.remain_duration = self.phases[init_phase_index].time

    def get_current_phase_index(self) -> int:
        return self.cur_phase_index

    def get_current_phase(self) -> LightPhase:
        return self.phases[self.cur_phase_index]

    def get_intersection(self) -> Intersection:
        return self.intersection

    def get_phases(self) -> List[LightPhase]:
        return self.phases

    def pass_time(self, seconds) -> None:
        if self.intersection and not self.intersection.is_virtual:
            self.remain_duration -= seconds
            while self.remain_duration <= 0.0:
                self.cur_phase_index = (self.cur_phase_index + 1) % len(self.phases)
                self.remain_duration += self.phases[self.cur_phase_index].time

    def set_phase(self, phase_index):
        self.cur_phase_index = phase_index

    def reset(self):
        self.init(0)
