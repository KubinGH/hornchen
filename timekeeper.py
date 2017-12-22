import sys
import time

print("Load debug time keeper")

# Apparently time.clock is more precise on Windows
# but, time.time is more precise on Linux.
gtime = time.clock if sys.platform == "win32" else time.time

class TValue:
    def __init__(self, value=0):
        self.value = value

class TimeKeeper:
    def __init__(self, the_time: TValue):
        self.the_time = the_time
        self.start = self.end = None

    def __enter__(self, *args):
        self.start = gtime()

    def __exit__(self, *args):
        self.end = gtime()
        self.the_time.value = self.end - self.start
