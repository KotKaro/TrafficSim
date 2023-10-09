import threading
import unittest

from src.utility.barrier import Barrier


class TestBarrier(unittest.TestCase):
    def test_wait_all_messages_added_when_all_threads_are_awaited_successfully(self):
        # Arrange
        num_threads = 3
        barrier = Barrier(num_threads)
        results = []

        def thread_function(thread_id):
            results.append(f"Thread {thread_id} is waiting at the barrier.")
            barrier.wait()
            results.append(f"Thread {thread_id} passed the barrier.")

        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=thread_function, args=(i,))
            threads.append(thread)

        # Act
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert
        self.assertEqual(len(results), num_threads * 2)  # Each thread should add two lines
        for i in range(num_threads):
            self.assertEqual(results.count(f"Thread {i} is waiting at the barrier."), 1)
            self.assertEqual(results.count(f"Thread {i} passed the barrier."), 1)


if __name__ == "__main__":
    unittest.main()
