# [file] infra/enums/model_type.py
from enum import Enum

class ModelType(str, Enum):
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content-based"
    DEEP_LEARNING = "deep-learning"