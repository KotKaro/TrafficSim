class VehicleInfo:
    def __init__(self, route=None):
        self.speed = 0
        self.len: float = 5
        self.width = 2
        self.max_pos_acc = 4.5
        self.max_neg_acc = 4.5
        self.usual_pos_acc = 2.5
        self.usual_neg_acc = 2.5
        self.min_gap = 2
        self.max_speed: float = 16.66667
        self.headway_time = 1
        self.yield_distance = 5
        self.turn_speed = 8.3333
        self.route = route
