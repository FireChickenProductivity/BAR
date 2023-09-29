from time import time

class TimeDifference:
    def __init__(self):
        self.last_timestamp: int = None
        self.last_difference: int = 0
    
    def receive_current_time(self) -> None:
        new_time: int = compute_current_time_in_seconds()
        self.receive_new_time(new_time)

    def receive_new_time(self, time: int) -> None:
        if self.last_timestamp:
            self.last_difference = time - self.last_timestamp
        self.last_timestamp = time
    
    def get_difference(self) -> int:
        return self.last_difference
    
def compute_current_time_in_seconds() -> int:
    return int(time())