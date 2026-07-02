class TaskStore:
    def __init__(self):
        self._store = {}

    def put(self, task_id: str, value):
        self._store[task_id] = value

    def get(self, task_id: str):
        return self._store.get(task_id)

    def delete(self, task_id: str):
        self._store.pop(task_id, None)

    def all(self):
        return dict(self._store)
