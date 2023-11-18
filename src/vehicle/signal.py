from src.roadnet.lane import Lane
from src.vehicle.vehicle import Vehicle


class Signal:
    def __init__(self):
        self.urgency: int = None
        self.direction: int = None  # -1 for left, 1 for right, 0 for unchanged
        self.target: Lane = None
        self.source: Vehicle = None
        self.response: int = 0
        self.extraSpace: float = 0
