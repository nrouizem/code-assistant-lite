from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Defines the common interface for agent execution.
    """
    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        """
        The main method to run the agent's task.
        """
        pass