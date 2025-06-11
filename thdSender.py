import threading
from datetime import datetime, timezone
from queue import Queue
import time

class thdSender(threading.Thread):
    def __init__(self, config, shared ):
        super().__init__()

        self.config = config
        self.shared = shared

        self.queue = self.shared['queue']
        self._stop_event = threading.Event()


    def run(self):
        print(f"[SENDER-RUN] ({datetime.now(tz=None)}) Starting Sender thread")

        try:
            while not self._stop_event.is_set():
                time.sleep(0.1)
            time.sleep(10)
        finally:
            print( f"[SENDER-RUN] ({datetime.now(tz=None)}) Sender thread stopped")

    def stop(self):
        print( f"[SENDER-STOP] ({datetime.now(tz=None)}) Stopping Sender thread")
        self._stop_event.set()

if __name__ == "__main__":
    pass
