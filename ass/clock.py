import threading
import time

class Timer:
    def __init__(self, timeout_seconds):
        self.timeout_seconds = timeout_seconds
        self.timer_thread = threading.Thread(target=self._timer_thread_func)
        self.timer_thread.daemon = True
        self.reset_event = threading.Event()
        self.timeout_event = threading.Event()
        self.stop_event = threading.Event()  # Added stop event
        self.is_running = False

    def _timer_thread_func(self):
        while True:
            self.is_running = True
            start_time = time.time()
            elapsed_time = 0

            while elapsed_time < self.timeout_seconds:
                if self.reset_event.wait(0.001):  # Wait for 1 millisecond
                    break

                elapsed_time = time.time() - start_time

            if elapsed_time >= self.timeout_seconds:
                self.timeout_event.set()

            self.reset_event.clear()
            self.is_running = False
            if self.stop_event.is_set():
                break  # End the thread

    def start(self):
        if not self.is_running:
            self.timer_thread.start()

    def stop(self):
        self.stop_event.set()  # Set the stop event
        self.reset_event.set()  # Trigger the reset event to exit possible waiting
        self.timer_thread.join()  # Wait for the thread to end
        self.is_running = False

    def reset(self):
        if self.is_running:
            self.reset_event.set()
            self.timeout_event.clear()

    def check_timeout(self):
        return self.timeout_event.is_set()
