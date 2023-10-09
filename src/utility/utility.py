import math
import random
import json
import os


class Point:
    eps = 1e-8

    @staticmethod
    def sign(x):
        return (x + Point.eps > 0) - (x < Point.eps)

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def len(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normal(self):
        return Point(-self.y, self.x)

    def unit(self):
        l = self.len()
        return Point(self.x / l, self.y / l)

    def ang(self):
        return math.atan2(self.y, self.x)

    def __mul__(self, k):
        return Point(self.x * k, self.y * k)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __neg__(self):
        return Point(-self.x, -self.y)


def cross_multiply(A, B):
    return A.x * B.y - A.y * B.x


def dot_multiply(A, B):
    return A.x * B.x + A.y * B.y


def calc_ang(A, B):
    ang = A.ang() - B.ang()
    pi = math.acos(-1)
    while ang >= pi / 2:
        ang -= pi / 2
    while ang < 0:
        ang += pi / 2
    return min(ang, pi - ang)


def on_segment(A, B, P):
    v1 = cross_multiply(B - A, P - A)
    v2 = dot_multiply(P - A, P - B)
    return Point.sign(v1) == 0 and v2 <= 0


def calc_intersect_point(A, B, C, D):
    P = A
    Q = C
    u = B - A
    v = D - C
    return P + u * (cross_multiply(Q - P, v) / cross_multiply(u, v))


def max2double(x, y):
    return max(x, y)


def min2double(x, y):
    return min(x, y)


def double2string(x):
    return str(x)


def generate_random_indices(n, rnd):
    randoms = list(range(n))
    random.shuffle(randoms)
    return randoms


def read_json_from_file(filename):
    try:
        with open(filename, 'r') as fp:
            data = json.load(fp)
        return data
    except (IOError, json.JSONDecodeError):
        return None


def write_json_to_file(filename, data):
    try:
        with open(filename, 'w') as fp:
            json.dump(data, fp, indent=4)
        return True
    except IOError:
        return False


class JsonFormatError(Exception):
    def __init__(self, info):
        super().__init__(info)


class JsonMemberMiss(JsonFormatError):
    def __init__(self, name):
        super().__init__(f"{name} is required but missing in JSON file")


class JsonTypeError(JsonFormatError):
    def __init__(self, name, type_str):
        super().__init__(f"{name}: expected type {type_str}")


def get_json_member_value(name, object):
    if name not in object:
        raise JsonMemberMiss(name)
    return object[name]


def get_json_member_object(name, object):
    value = get_json_member_value(name, object)
    if not isinstance(value, dict):
        raise JsonTypeError(name, "object")
    return value


def get_json_member_array(name, object):
    value = get_json_member_value(name, object)
    if not isinstance(value, list):
        raise JsonTypeError(name, "array")
    return value


def json_convertable_to(value, target_type):
    if target_type == float:
        # We do not differentiate between 123.0 and 123
        return isinstance(value, (int, float))
    return isinstance(value, target_type)
