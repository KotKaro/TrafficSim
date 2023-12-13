import json
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from typing import List

from src.flow.flow import Flow
from src.flow.route import Route
from src.roadnet.drivable import Drivable
from src.roadnet.intersection import Intersection
from src.roadnet.road import Road
from src.roadnet.roadnet import RoadNet
from src.utility.utility import read_json_from_file, write_json_to_file
from src.vehicle.vehicle import Vehicle
from src.vehicle.vehicle_info import VehicleInfo


class Engine:

    def __init__(self, config_file: str, thread_num: int):
        self.interval: float
        self.warnings: bool
        self.rlTrafficLight: bool
        self.laneChange: bool
        self.seed: int
        self.dir: str
        self.road_net: RoadNet
        self.saveReplayInConfig: bool
        self.saveReplay: bool

        self.thread_num = thread_num
        self.thread_vehicle_pool: List[List[Vehicle]] = [[] for _ in range(thread_num)]
        self.thread_road_pool: List[List[Road]] = [[] for _ in range(thread_num)]
        self.thread_intersection_pool: List[List[Intersection]] = [[] for _ in range(thread_num)]
        self.thread_drivable_pool: List[List[Drivable]] = [[] for _ in range(thread_num)]
        self.flows: List[Flow] = []

        success = self.load_config(config_file)
        if not success:
            print("load config failed!")

        self.thread_pool = ThreadPoolExecutor(max_workers=thread_num)
        self.threads = []
        for i in range(thread_num):
            t = threading.Thread(target=self.thread_controller, args=(
                self.thread_vehicle_pool[i],
                self.thread_road_pool[i],
                self.thread_intersection_pool[i],
                self.thread_drivable_pool[i]))
            self.threads.append(t)
            t.start()

    def thread_controller(self, vehicle_pool, road_pool, intersection_pool, drivable_pool):
        # Thread specific processing logic
        pass

    def load_config(self, config_file: str) -> bool:
        document = read_json_from_file(config_file)
        if read_json_from_file is None:
            print("cannot open config file!")
            return False

        # if (!document.IsObject()) {
        #     std::cerr << "wrong format of config file" << std::endl;
        #     return false;
        # }

        try:
            self.interval = document.interval
            self.warnings = False
            self.rlTrafficLight = document.rlTrafficLight
            self.laneChange = document.laneChange if document.laneChange is not None else False
            self.seed = document.seed
            np.random.seed(self.seed)
            self.dir = document.dir
            roadnet_file: str = document.roadnetFile
            flowFile: str = document.flowFile

            if self.loadRoadNet(self.dir + roadnet_file) is False:
                print("loading roadnet file error!")
                return False

            if self.load_flow(self.dir + flowFile) is False:
                print("loading flow file error!")
                return False

            if self.warnings:
                self.checkWarning()

            self.saveReplayInConfig = document.saveReplay
            self.saveReplay = document.saveReplay

            if self.saveReplay:
                roadnetLogFile: str = document.roadnetLogFile
                replayLogFile: str = document.replayLogFile
                self.setLogFile(self.dir + roadnetLogFile, self.dir + replayLogFile)
        except:
            return False
        self.stepLog = ""
        return True

    def loadRoadNet(self, json_file: str) -> bool:
        self.road_net = RoadNet()
        ans = self.road_net.load_from_json(json_file)
        cnt = 0
        for road in self.road_net.get_roads():
            self.thread_road_pool[cnt].append(road)
            cnt = (cnt + 1) % self.thread_num

        for intersection in self.road_net.get_intersections():
            self.thread_intersection_pool[cnt].append(intersection)
            cnt = (cnt + 1) % self.thread_num

        for drivable in self.road_net.get_drivables():
            self.thread_drivable_pool[cnt].append(drivable)
            cnt = (cnt + 1) % self.thread_num

        self.json_root = self.road_net.convert_to_json()
        return ans

    def load_flow(self, json_filename: str):
        try:
            root = read_json_from_file(json_filename)

            if not isinstance(root, list):
                raise TypeError("flow file must be an array")

            for i, flow in enumerate(root):
                roads = Route()
                for road_name in flow["route"]:
                    if not isinstance(road_name, str):
                        raise TypeError("route must be a string")
                    road = self.road_net.get_road_by_id(road_name)
                    if not road:
                        raise ValueError(f"No such road: {road_name}")
                    roads.route.append(road)

                vehicle_info = VehicleInfo()
                vehicle_info.len = flow["vehicle"]["length"]
                vehicle_info.width = flow["vehicle"]["width"]
                vehicle_info.max_pos_acc = flow["vehicle"]["maxPosAcc"]
                vehicle_info.max_neg_acc = flow["vehicle"]["maxNegAcc"]
                vehicle_info.usual_pos_acc = flow["vehicle"]["usualPosAcc"]
                vehicle_info.usual_neg_acc = flow["vehicle"]["usualNegAcc"]
                vehicle_info.min_gap = flow["vehicle"]["minGap"]
                vehicle_info.max_speed = flow["vehicle"]["maxSpeed"]
                vehicle_info.headway_time = flow["vehicle"]["headwayTime"]
                vehicle_info.route = roads

                start_time = flow.get("startTime", 0)
                end_time = flow.get("endTime", -1)

                new_flow = Flow(
                    vehicleInfo=vehicle_info,
                    time_interval=flow["interval"],
                    engine=self,
                    start_time=start_time,
                    end_time=end_time,
                    id=f"flow_{i}"
                )

                self.flows.append(new_flow)

        except (IOError, json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"Error occurred when reading flow file: {e}")
            return False

        return True

    def rnd(self):
        pass

    def checkPriority(self, priority: int):
        pass

    def pushVehicle(self, vehicle: Vehicle, pushToDrivable: bool):
        pass

    def get_current_time(self) -> float:
        pass

    def get_interval(self) -> float:
        pass

    def checkWarning(self):
        result = True

        if self.interval < 0.2 or self.interval > 1.5:
            print("Deprecated time interval, recommended interval between 0.2 and 1.5")
            result = False


        for lane in self.road_net.get_lanes():
            if lane.get_length() < 50:
                print("Deprecated road length, recommended road length at least 50 meters")
                result = False

            if lane.get_max_speed() > 30:
                print("Deprecated road max speed, recommended max speed at most 30 meters/s")
                result = False

        return result

    def setLogFile(self, json_file: str, log_file: str):
        if write_json_to_file(json_file, self.json_root) is False:
            print("write roadnet log file error")
        open(log_file, 'w')
