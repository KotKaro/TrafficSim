from typing import List
from vehicle import Vehicle

from src.roadnet.drivable import Drivable


class Buffer:
    isDisSet: bool = False
    isSpeedSet: bool = False
    isDrivableSet: bool = False
    isNotifiedVehicles: bool = False
    isEndSet: bool = False
    isEnterLaneLinkTimeSet: bool = False
    isBlockerSet: bool = False
    isCustomSpeedSet: bool = False
    dis: float
    deltaDis: float
    speed: float
    customSpeed: float
    drivable: Drivable
    notifiedVehicles: List[Vehicle]
    end: bool
    blocker: Vehicle = None
    enterLaneLinkTime: int
