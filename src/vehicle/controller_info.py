import sys

from src.flow.route import Route
from src.roadnet.drivable import Drivable
from src.vehicle.router import Router
from src.vehicle.vehicle import Vehicle


class ControllerInfo:
    def __init__(self, vehicle: Vehicle, route: Route = None, rnd=None, other: 'ControllerInfo' = None):
        if other is not None:
            # TODO consider copy functionality
            self.dis: float = other.dis
            self.drivable: Drivable = other.drivable
            self.prevDrivable: Drivable = other.prevDrivable
            self.approachingIntersectionDistance: float = other.approachingIntersectionDistance
            self.gap: float = other.gap
            self.enterLaneLinkTime: int = other.enterLaneLinkTime
            self.leader: Vehicle = other.leader
            self.blocker: Vehicle = other.blocker
            self.end: bool = other.end
            self.running: bool = other.running
            self.router: Router = Router(vehicle, other.router.route, other.router.rnd)
            self.router.set_vehicle(vehicle)
        else:
            self.dis: float = 0
            self.drivable: Drivable = None
            self.prevDrivable: Drivable = None
            self.approachingIntersectionDistance: float = 0
            self.gap: float = 0
            self.enterLaneLinkTime: int = sys.maxsize
            self.leader: Vehicle = None
            self.blocker: Vehicle = None
            self.end: bool = False
            self.running: bool = False
            self.router: Router = Router(vehicle, route, rnd)
