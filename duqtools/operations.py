from queue import SimpleQueue
from typing import Callable

from overloading import overload
from pydantic import Field

from .schema import BaseModel


class Operation(BaseModel):
    description: str = Field(
        description='description of the operation to be done')
    action: Callable = Field(
        description='a function which can be executed when we '
        'decide to apply this operation')


class Operations(SimpleQueue):
    """Operations Queue which keeps track of all the operations that need to be
    done."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Operations._instance:
            Operations._instance = object.__new__(cls)
        return Operations._instance

    @overload
    def put(self, item: Operation) -> None:
        """Restrict our diet to Operation objects only."""
        super().put(self, item)

    def apply(self):
        """Apply the next operation in the queue and remove it."""
        self.get()()

    def apply_all(self):
        """Apply all queued operations and empty the queue."""
        while not self.empty():
            self.apply()


op_queue = Operations()
