from abc import ABC, abstractmethod


class IEvaluator(ABC):
    @abstractmethod
    def evaluate(self, strategy):
        raise NotImplementedError
