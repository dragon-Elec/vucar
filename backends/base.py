# src/vucar/backends/base.py
from abc import ABC, abstractmethod
from pathlib import Path

class Backend(ABC):
    """
    Abstract Base Class for all execution backends.
    Defines the contract that all backends must follow.
    """
    @abstractmethod
    def execute(self, video_path: Path, command: str):
        """
        The main method to execute the video processing task.
        This method must be implemented by all subclasses.
        """
        pass
