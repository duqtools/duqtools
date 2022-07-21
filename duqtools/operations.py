from __future__ import annotations

import logging
from queue import SimpleQueue
from typing import Callable

from pydantic import Field

from .schema import BaseModel

logger = logging.getLogger(__name__)


class Operation(BaseModel):
    """Operation, simple class which has a callable action."""

    description: str = Field(
        description='description of the operation to be done')
    action: Callable = Field(
        description='a function which can be executed when we '
        'decide to apply this operation')

    def __call__(self) -> Operation:
        logger.info(f'-: {self.description}')
        self.action()
        return self


class Operations(SimpleQueue):
    """Operations Queue which keeps track of all the operations that need to be
    done."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Operations._instance:
            Operations._instance = super().__new__(cls)
        return Operations._instance

    def add(self, action: Callable, description: str) -> None:
        """convenience wrapper around put."""

        self.put(Operation(action=action, description=description))

    def put(self, item: Operation) -> None:  # type: ignore
        """Restrict our diet to Operation objects only."""

        super().put(item)

    def apply(self) -> Operation:
        """Apply the next operation in the queue and remove it."""

        return self.get()()

    def apply_all(self) -> None:
        """Apply all queued operations and empty the queue."""
        while not self.empty():
            self.apply()


op_queue = Operations()


def confirm_operations(func):
    """Decorator which confirms and applies queued operations after the
    function."""

    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        op_queue.apply_all()
        return ret

    return wrapper
