import time


class EventStore:
    def __init__(self):
        self.events = []

    def append(self, stage, action, input_data=None, output=None):
        self.events.append({
            "step": len(self.events),
            "stage": stage,
            "action": action,
            "input": input_data or {},
            "output": output or {},
            "ts": time.time(),
        })

    def dump(self):
        return self.events
