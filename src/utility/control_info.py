from src.roadnet.lane import Lane


class ControlInfo:
    def __init__(self, speed: float = 0.0):
        speed: float = speed
        changing_speed: float = 0.0
        next_lane: Lane = None
        waiting_for_changing_lane: bool = False
        collision: bool = False
