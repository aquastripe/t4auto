from abc import ABC, abstractmethod
from typing import NoReturn


class Configurable(ABC):

    @abstractmethod
    def load_config(self, config: dict) -> NoReturn:
        ...

    @abstractmethod
    def dump_config(self) -> dict:
        ...
