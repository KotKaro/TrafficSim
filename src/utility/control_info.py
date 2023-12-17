from src.roadnet.lane import Lane


class ControlInfo:
    def __init__(self, speed: float = 0.0):
        self.speed: float = speed
        self.changing_speed: float = 0.0
        self.next_lane: Lane = None
        self.waiting_for_changing_lane: bool = False
        self.collision: bool = False
