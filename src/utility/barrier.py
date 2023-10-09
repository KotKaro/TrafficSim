import threading


class Barrier:
    def __init__(self, num_threads):
        self.num_threads = num_threads
        self.count = 0
        self.mutex = threading.Lock()
        self.cv = threading.Condition(lock=self.mutex)

    def wait(self):
        with self.mutex:
            self.count += 1
            if self.count == self.num_threads:
                self.cv.notify_all()
            while self.count < self.num_threads:
                self.cv.wait()
