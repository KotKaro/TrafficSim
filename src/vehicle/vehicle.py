from src.roadnet.road import Road


class Vehicle:

    def __init__(self):
        pass

    def get_distance(self) -> float:
        pass

    def set_segment_index(self, index: int):
        pass

    def get_len(self):
        pass

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
