from src.flow.route import Route
from src.vehicle.vehicle import Vehicle


class LaneChangeInfo:
    def __init__(self, vehicle: Vehicle, route: Route = None, rnd=None, other: 'ControllerInfo' = None):
        self.partnerType: int = 0  # 0 for no partner; 1 for real vehicle; 2 for shadow vehicle;
        self.partner: Vehicle | None = None
        self.offset: float = 0
        self.segmentIndex: int = 0
