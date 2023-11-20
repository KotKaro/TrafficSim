from typing import List

from src.roadnet.road import Road


class Route:

    def __init__(self):
        self.route: List[Road] = []

    def begin(self):
        pass

    def get_route(self) -> List[Road]:
        return self.route
