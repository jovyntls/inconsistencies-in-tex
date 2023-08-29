from enum import Enum

class Log_level(Enum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    NONE = 5

class Logger:
    def __init__(self, log_level):
        self.log_level = log_level

    def log(self, log_level, message):
        def should_log(log_level):
            return log_level.value - self.log_level.value >= 0
        if should_log(log_level): print(message)

