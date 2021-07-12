
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 16:11:01 2020

@author: chandan
"""

import heapq
import time
from progressbar import Bar, ETA, ProgressBar, RotatingMarker


def get_stop_condition(time_condition, runtime, max_iterations):
    if time_condition:
        stop_time = time.time() + runtime
        def stop_condition(_):
            return time.time() >= stop_time
    else:
        def stop_condition(iterations):
            return iterations >= max_iterations
    return stop_condition

def _run_progress_bar(seconds):
    time.sleep(.5)
    widgets = [Bar(marker=RotatingMarker()), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=seconds).start()
    for i in range(seconds):
        time.sleep(.98)
        pbar.update(i)
    pbar.finish()
    
def check_machine_availability(machine_list):
    unavailable_machine_list = []
    for machine in machine_list:
        if machine.get_status().lower() == 'broken':
            unavailable_machine_list.append(int(machine.machine_name))
    return unavailable_machine_list


class Heap:

    def __init__(self, max_heap=False):
        self._heap = []
        self._is_max_heap = max_heap

    def push(self, obj):
        if self._is_max_heap:
            heapq.heappush(self._heap, MaxHeapObj(obj))
        else:
            heapq.heappush(self._heap, obj)

    def pop(self):
        if self._is_max_heap:
            return heapq.heappop(self._heap).val
        else:
            return heapq.heappop(self._heap)

    def __getitem__(self, i):
        return self._heap[i].val

    def __len__(self):
        return len(self._heap)


class MaxHeapObj:

    def __init__(self, val):
        self.val = val

    def __lt__(self, other):
        return self.val > other.val

    def __gt__(self, other):
        return self.val < other.val

    def __eq__(self, other):
        return self.val == other.val