import math
import os
import unittest
import tempfile

from src.utility.utility import Point, JsonMemberMiss, JsonTypeError, cross_multiply, dot_multiply, calc_ang, on_segment, calc_intersect_point, \
    max2double, generate_random_indices, read_json_from_file, write_json_to_file, double2string, min2double, \
    get_json_member_value, get_json_member_value, get_json_member_array, get_json_member_object, json_convertable_to


class TestPoint(unittest.TestCase):
    def test_len_returns_square_root_of_multiplied_edges(self):
        # Arrange
        sut = Point(2, 3)

        # Act
        result = sut.len()

        # Assert
        self.assertEqual(result, math.sqrt(13))

    def test_normal_swaps_x_with_y_and_y_is_multiplied_by_minus_one(self):
        # Arrange
        sut = Point(2, 3)

        # Act
        new_point = sut.normal()

        # Assert
        self.assertEqual(sut.x, new_point.y)
        self.assertEqual(sut.y, -new_point.x)

    def test_unit_returns_point_which_coordinates_are_divided_by_length(self):
        # Arrange
        sut = Point(5, 4)

        # Act
        new_point = sut.unit()

        # Assert
        self.assertEqual(new_point.x, 5 / math.sqrt(41))
        self.assertEqual(new_point.y, 4 / math.sqrt(41))

    def test_ang_returns_angle_between_point_and_x_axis(self):
        # Arrange
        sut = Point(1, 1)

        # Act
        result = sut.ang()

        # Assert

        self.assertEqual(result, math.pi / 4)

    def test_mul_returns_point_with_multiplied_coordinates(self):
        # Arrange
        sut = Point(1, 2)

        # Act
        result = sut * 3

        # Assert
        self.assertEqual(result.x, 3)
        self.assertEqual(result.y, 6)

    def test_sub_returns_point_with_subtracted_coordinates(self):
        # Arrange
        sut = Point(1, 2)

        # Act
        result = sut - Point(3, 4)

        # Assert
        self.assertEqual(result.x, -2)
        self.assertEqual(result.y, -2)

    def test_add_returns_point_with_added_coordinates(self):
        # Arrange
        sut = Point(1, 2)

        # Act
        result = sut + Point(3, 4)

        # Assert
        self.assertEqual(result.x, 4)
        self.assertEqual(result.y, 6)

    def test_neg_returns_point_with_negated_coordinates(self):
        # Arrange
        sut = Point(1, 2)

        # Act
        result = -sut

        # Assert
        self.assertEqual(result.x, -1)
        self.assertEqual(result.y, -2)

    def test_sign_returns_1_when_x_is_greater_than_eps(self):
        # Arrange
        sut = Point(1, 0)

        # Act
        result = Point.sign(sut.x)

        # Assert
        self.assertEqual(result, 1)


class TestUtilityDefs(unittest.TestCase):
    def test_returns_cross_product_of_two_points(self):
        # Arrange
        point_a = Point(1, 2)
        point_b = Point(3, 4)

        # Act
        result = cross_multiply(point_a, point_b)

        # Assert
        self.assertEqual(result, -2)

    def test_dot_multiply_product_of_two_points(self):
        # Arrange
        point_a = Point(1, 2)
        point_b = Point(3, 4)

        # Act
        result = dot_multiply(point_a, point_b)

        # Assert
        self.assertEqual(result, 11)

    def test_calc_ang_there_is_90_degree_between_points_result_is_zero(self):
        # Arrange
        point_a = Point(0, 5)
        point_b = Point(5, 0)

        # Act
        result = calc_ang(point_a, point_b)

        # Assert
        self.assertEqual(result, 0)

    def test_calc_ang_there_are_points_with_same_coordinates_result_is_zero(self):
        # Arrange
        point_a = Point(3, 3)
        point_b = Point(3, 3)

        # Act
        result = calc_ang(point_a, point_b)

        # Assert
        self.assertEqual(result, 0)

    def test_calc_ang_there_are_points_with_same_coordinates_result_is_zero1(self):
        # Arrange
        point_a = Point(3, 0)
        point_b = Point(6, 0)

        # Act
        result = calc_ang(point_a, point_b)

        # Assert
        self.assertEqual(result, 0)

    def test_on_segment_returns_true_when_point_is_on_segment(self):
        # Arrange
        A = Point(0, 0)
        B = Point(5, 0)
        P = Point(3, 0)

        # Act
        result = on_segment(A, B, P)

        # Assert
        self.assertTrue(result)

    def test_on_segment_returns_false_when_point_is_not_on_segment(self):
        # Arrange
        A = Point(0, 0)
        B = Point(5, 0)
        P = Point(6, 0)

        # Act
        result = on_segment(A, B, P)

        # Assert
        self.assertFalse(result)

    def test_calc_intersect_point_returns_point_of_intersection(self):
        # Arrange
        A = Point(1, 1)
        B = Point(2, 2)
        C = Point(3, 3)
        D = Point(4, 5)

        # Act
        result = calc_intersect_point(A, B, C, D)

        # Assert
        self.assertEqual(result.x, 3)
        self.assertEqual(result.y, 3)

    def test_max2double_returns_greater_number(self):
        # Arrange
        x = 1
        y = 2

        # Act
        result = max2double(x, y)

        # Assert
        self.assertEqual(result, 2)

    def test_min2double_returns_smaller_number(self):
        # Arrange
        x = 1
        y = 2

        # Act
        result = min2double(x, y)

        # Assert
        self.assertEqual(result, 1)

    def test_double2string_returns_string(self):
        # Arrange
        x = 1

        # Act
        result = double2string(x)

        # Assert
        self.assertEqual(result, "1")

    def test_generate_random_indices_returns_list_of_random_indices_of_given_length(self):
        # Arrange
        n = 10
        rnd = 1

        # Act
        result = generate_random_indices(n, rnd)

        # Assert
        self.assertEqual(len(result), n)
        self.assertTrue(all([0 <= x < n for x in result]))

    def test_read_json_from_file_returns_json(self):
        # Arrange
        new_file, filename = tempfile.mkstemp()
        os.write(new_file, bytes('{"test": "test"}', 'utf-8'))
        os.close(new_file)

        # Act
        result = read_json_from_file(filename)

        # Assert
        self.assertEqual(result, {"test": "test"})
        os.remove(filename)

    def test_write_json_to_file_writes_json_to_file(self):
        # Arrange
        new_file, filename = tempfile.mkstemp()
        os.close(new_file)

        # Act
        write_json_to_file(filename, {"test": "test"})

        # Assert
        self.assertEqual(read_json_from_file(filename), {"test": "test"})
        os.remove(filename)

    def test_get_json_member_value_returns_value_of_member(self):
        # Arrange
        object = {"test": "test1"}

        # Act
        result = get_json_member_value("test", object)

        # Assert
        self.assertEqual(result, "test1")

    def test_get_json_member_value_raises_JsonMemberMiss_if_property_is_missing_in_object(self):
        # Arrange§
        object = {"test": "test1"}

        # Act
        with self.assertRaises(JsonMemberMiss):
            # Assert
            get_json_member_value("test1", object)

    def test_get_json_member_object_returns_object_of_member(self):
        # Arrange
        object = {"test": {"test1": "test2"}}

        # Act
        result = get_json_member_object("test", object)

        # Assert
        self.assertEqual(result, {"test1": "test2"})

    def test_get_json_member_object_raises_JsonTypeError_if_property_is_not_a_dict(self):
        # Arrange
        object = {"test": "not a dict"}

        # Act
        with self.assertRaises(JsonTypeError):
            # Assert
            get_json_member_object("test", object)

    def test_get_json_member_array_returns_array_of_member(self):
        # Arrange
        object = {"test": ["test1", "test2"]}

        # Act
        result = get_json_member_array("test", object)

        # Assert
        self.assertEqual(result, ["test1", "test2"])

    def test_get_json_member_array_raises_JsonTypeError_if_property_is_not_an_array(self):
        # Arrange
        object = {"test": "test"}

        # Act
        with self.assertRaises(JsonTypeError):
            # Assert
            get_json_member_array("test", object)

    def test_json_convertable_to_returns_true_if_string_is_provided_and_trying_convert_to_str(self):
        # Arrange
        value = "test"
        target_type = str

        # Act
        result = json_convertable_to(value, target_type)

        # Assert
        self.assertTrue(result)

    def test_json_convertable_to_returns_false_if_number_is_provided_and_trying_convert_to_str(self):
        # Arrange
        value = 1
        target_type = str

        # Act
        result = json_convertable_to(value, target_type)

        # Assert
        self.assertFalse(result)

    def test_json_convertable_to_returns_true_when_trying_to_convert_number_to_float(self):
        # Arrange
        value = 1
        target_type = float

        # Act
        result = json_convertable_to(value, target_type)

        # Assert
        self.assertTrue(result)



if __name__ == "__main__":
    unittest.main()
