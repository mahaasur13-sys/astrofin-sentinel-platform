from .api import app as InferenceAPI
from .predictor import Predictor

__all__ = ["Predictor", "InferenceAPI"]
