from time import time

class TimeDifference:
    def __init__(self):
        self.last_timestamp = None
        self.last_difference = 0
    
    def receive_current_time(self):
        new_time = compute_current_time_in_seconds()
        self.receive_new_time(new_time)

    def receive_new_time(self, time):
        if self.last_timestamp:
            self.last_difference = time - self.last_timestamp
        self.last_timestamp = time
    
    def get_difference(self):
        return self.last_difference
    
def compute_current_time_in_seconds():
    return int(time())