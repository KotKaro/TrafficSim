from typing import List

from src.vehicle.vehicle import Vehicle


class Segment:
    def __init__(self, index, belong_lane, start_pos, end_pos):
        self.index = index
        self.belong_lane = belong_lane
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.vehicles = []

    def get_start_pos(self):
        return self.start_pos

    def get_end_pos(self):
        return self.end_pos

    def get_index(self):
        return self.index

    def get_vehicles(self) -> List[Vehicle]:
        return self.vehicles

    def find_vehicle(self, vehicle):
        for v in self.vehicles:
            if v == vehicle:
                return v
        return None

    def remove_vehicle(self, vehicle):
        for v in self.vehicles:
            if v == vehicle:
                self.vehicles.remove(v)
                return

    def insert_vehicle(self, vehicle):
        index = 0
        for v in self.vehicles:
            if v.get_distance() > vehicle.get_distance():
                break
            index += 1
        self.vehicles.insert(index, vehicle)