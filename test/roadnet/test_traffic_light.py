import unittest

from src.roadnet.traffic_light import TrafficLight, Intersection, LightPhase


class TestTrafficLight(unittest.TestCase):
    def setUp(self):
        self.sut = TrafficLight()

    def test_init_should_set_phase_index_and_remain_duration_to_zero(self):
        # Act
        self.sut.init(0)

        # Assert
        self.assertEqual(self.sut.cur_phase_index, 0)
        self.assertEqual(self.sut.remain_duration, 0.0)

    def test_get_current_phase_index_should_return_current_phase_index(self):
        # Act
        self.sut.cur_phase_index = 1

        # Assert
        self.assertEqual(self.sut.get_current_phase_index(), 1)

    def test_get_current_phase_should_return_current_phase(self):
        # Arrange
        self.sut.phases = [1, 2, 3]
        self.sut.cur_phase_index = 1

        # Act
        result = self.sut.get_current_phase()

        # Assert
        self.assertEqual(result, 2)

    def test_get_intersection_should_return_intersection(self):
        # Arrange
        self.sut.intersection = 1

        # Act
        result = self.sut.get_intersection()

        # Assert
        self.assertEqual(result, 1)

    def test_get_phase_should_return_phases(self):
        # Arrange
        self.sut.phases = [1, 2, 3]

        # Act
        result = self.sut.get_phases()

        # Assert
        self.assertEqual(result, [1, 2, 3])

    def test_pass_time_should_decrease_remain_duration_of_current_phase(self):
        # Arrange
        intersection = Intersection()
        intersection.is_virtual = False
        self.sut.intersection = intersection
        self.sut.phases = [LightPhase(), LightPhase(), LightPhase()]
        self.sut.phases[2].time = 10

        self.sut.init(2)

        # Act
        self.sut.pass_time(2)

        # Assert
        self.assertEqual(8, self.sut.remain_duration)

    def test_pass_time_should_go_to_next_phase_if_current_phase_timed_out_and_decrease_next_phase(self):
        # Arrange
        self.sut.intersection = lambda: None
        self.sut.intersection.is_virtual = False
        self.sut.phases = [lambda: None, lambda: None, lambda: None]
        self.sut.phases[0].time = 55
        self.sut.phases[1].time = 1
        self.sut.phases[2].time = 4

        self.sut.init(2)

        # Act
        self.sut.pass_time(8)

        # Assert
        self.assertEqual(51, self.sut.remain_duration)

    def test_set_phase_should_set_phase_index(self):
        # Act
        self.sut.set_phase(1)

        # Assert
        self.assertEqual(self.sut.cur_phase_index, 1)

    def test_reset_should_init_again_with_zero(self):
        # Arrange
        self.sut.init(1)

        # Act
        self.sut.reset()

        # Assert
        self.assertEqual(self.sut.cur_phase_index, 0)
        self.assertEqual(self.sut.remain_duration, 0.0)
