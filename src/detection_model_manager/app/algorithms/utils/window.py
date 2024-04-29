"""
    Window: A class that emulates a sliding window through the system calls trace
    ====

    size {int}: the size of the window to use
"""


class Window:

    def __init__(self, size: int):
        self.window = []
        self.size = size

    def add(self, item):
        if self.is_full():
            self.pop()
        self.window.append(item)

    def pop(self):
        self.window = self.window[1:]

    def is_empty(self) -> bool:
        return len(self.window) == 0

    def get_window(self) -> list:
        return self.window

    def __str__(self):
        return self.window

    def get_size(self) -> int:
        return self.size

    def is_full(self) -> bool:
        return len(self.window) == self.size
