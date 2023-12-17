from src.engine.engine import Engine
from src.vehicle.vehicle import Vehicle
from src.vehicle.vehicle_info import VehicleInfo


class Flow:
    def __init__(self, vehicleInfo: VehicleInfo,
                 time_interval: float,
                 engine: Engine,
                 start_time: int,
                 end_time: int,
                 id: str):
        self.current_time = 0
        assert time_interval >= 1 or start_time == end_time
        self.vehicleInfo: VehicleInfo = vehicleInfo
        self.interval: float = time_interval
        self.engine: Engine = engine
        self.start_time: int = start_time
        self.end_time: int = end_time
        self.id: str = id
        self.now_time: float = time_interval
        self.valid: bool = False
        self.cnt: int = 0

    def nextStep(self, timeInterval: float) -> None:
        if self.valid is False:
            return

        if self.end_time != -1 and self.current_time > self.end_time:
            return

        if self.current_time >= self.start_time:
            while self.now_time >= self.interval:
                vehicle = Vehicle(self.vehicleInfo, id + "_" + self.cnt, self.engine, self)
                self.cnt += 1
                priority = vehicle.get_priority()

                while self.engine.check_priority(priority):
                    priority = self.engine.rnd()

                vehicle.set_priority(priority)
                self.engine.pushVehicle(vehicle, False)
                vehicle.get_first_road().add_plan_route_vehicle(vehicle)
                self.now_time -= self.interval
            self.now_time += timeInterval
        self.current_time += timeInterval

    def getId(self) -> str:
        return self.id

    def isValid(self) -> str:
        return self.valid

    def setValid(self, valid: bool) -> None:
        if self.valid and valid is False:
            print(f"[warning] Invalid route '{self.id}'. Omitted by default.")
        self.valid = valid;

    def reset(self) -> None:
        self.now_time = self.time_interval
        self.current_time = 0
        self.cnt = 0
