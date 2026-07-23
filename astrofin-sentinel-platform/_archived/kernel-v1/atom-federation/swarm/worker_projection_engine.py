from typing import Any, List


class ProjectedAxis:
    def __init__(self, name: str = "axis"):
        self.name = name
        self.vector: List[Any] = []

    def project(self, data: Any):
        self.vector.append(data)
        return self.vector
