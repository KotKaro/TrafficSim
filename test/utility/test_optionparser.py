import threading
import unittest

from src.utility.optionparser import OptionParser, StorageMode


class TestOptionParser(unittest.TestCase):
    def test_add_option_returns_option_with_given_flags(self):
        # Arrange
        sut = OptionParser()

        # Act
        result = sut.add_option("--long", "-l")

        # Assert
        self.assertEqual(result.long_flag(), "--long")
        self.assertEqual(result.short_flag(), "-l")

    def test_get_value_raises_key_error_if_option_is_not_set(self):
        # Arrange
        sut = OptionParser()

        # Act + Assert
        self.assertRaises(KeyError, sut.get_value, "--long")

    def test_get_value_returns_false_default_value_value_if_option_was_added(self):
        # Arrange
        sut = OptionParser()
        sut.add_option("--long", "-l")

        # Act
        val = sut.get_value("-long")

        # Act + Assert
        self.assertEqual(val, False)

    def test_get_value_str(self):
        # Arrange
        sut = OptionParser()
        option = sut.add_option("--test", "-t").mode(StorageMode.STORE_VALUE)

        # Act
        sut.eat_arguments(["script.py", "--test"])

        # Assert
        self.assertEqual(sut.get_value_str("test"), "value")


if __name__ == "__main__":
    unittest.main()
