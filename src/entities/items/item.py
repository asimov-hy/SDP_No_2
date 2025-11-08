from abc import ABC, abstractmethod

from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity


class Item(BaseEntity, ABC):
    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image):
        super().__init__(x, y, image)

    @abstractmethod
    def apply_effect(self):
        pass