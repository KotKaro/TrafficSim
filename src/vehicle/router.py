from src.roadnet.drivable import Drivable


class Router:
    def set_vehicle(self, vehicle):
        pass

    def update(self):
        pass

    def on_last_road(self) -> bool:
        pass

    def get_next_drivable(self, curLane: Drivable) -> Drivable:
        pass
