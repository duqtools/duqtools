from __future__ import annotations

import logging
from collections import deque
from typing import Callable

import click
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


class Operations(deque):
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

        self.append(Operation(action=action, description=description))

    def append(self, item: Operation) -> None:  # type: ignore
        """Restrict our diet to Operation objects only."""

        super().append(item)

    def apply(self) -> Operation:
        """Apply the next operation in the queue and remove it."""

        return self.popleft()()

    def apply_all(self) -> None:
        """Apply all queued operations and empty the queue."""
        while len(self) != 0:
            self.apply()

    def confirm_apply_all(self) -> bool:
        """First asks the user if he wants to apply everything.

        Returns
        -------
        bool: did we apply everything or not
        """

        # To print the descriptions we need to get them
        logger.info('')
        logger.info('Operations in the Queue:')
        logger.info('========================')
        for op in self:
            logging.info(op.description)

        ans = click.confirm('Do you want to apply all these operations?',
                            default=False)
        if ans:
            self.apply_all()
        return ans


op_queue = Operations()


def confirm_operations(func):
    """Decorator which confirms and applies queued operations after the
    function."""

    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        op_queue.confirm_apply_all()
        return ret

    return wrapper
