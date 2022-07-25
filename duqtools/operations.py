from __future__ import annotations

import logging
from collections import deque
from inspect import signature
from typing import Callable

import click
from pydantic import Field

from .schema import BaseModel

logger = logging.getLogger(__name__)


class Operation(BaseModel):
    """Operation, simple class which has a callable action.

    Usually not called directly but used through Operations. has the
    following members:
    """

    description: str = Field(
        description='description of the operation to be done')
    action: Callable = Field(
        description='a function which can be executed when we '
        'decide to apply this operation')
    args: tuple = Field((),
                        description='positional arguments that have to be '
                        'passed to the action')
    kwargs: dict = Field(None,
                         description='keyword arguments that will be '
                         'passed to the action')

    def __init__(self, action, description, *args, **kwargs):
        """__init__.

        Parameters
        ----------
        description: str
            description of the operation to be done
        action: Callable
            function to be eventually evaluated
        *args: tuple
            positional arguments to action
        **kwargs: dict
            keyword arguments to action
        """
        super().__init__(action=action,
                         description=description,
                         *args,
                         **kwargs)
        if not self.kwargs:
            self.kwargs = {}

    def __call__(self) -> Operation:
        """Execute the action with the args and kwargs.

        Returns
        -------
        Operation
            The operation that was executed
        """
        logger.info(self.description)
        self.action(*self.args, **self.kwargs)
        return self


class Operations(deque):
    """Operations Queue which keeps track of all the operations that need to be
    done.

    It's basically dask_delayed, but custom made and a few drawbacks:
    The return value from an action is eventually discarded,
    communication between queue items is possible through references, or
    global values, but not really recommended, and no guidance for this
    is provided
    """

    _instance = None
    yes = False  # Apply operations without prompt
    dry_run = False  # Never apply any operations (do not even ask)

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Operations._instance:
            Operations._instance = super().__new__(cls)
        return Operations._instance

    def add(self, *args, **kwargs) -> None:
        """convenience Operation wrapper around put.

        ```python
        from duqtools.operations import add_to_op_queue.

        op_queue.add(print, args=('Hello World,),
                description="Function that prints hello world")
        ```
        """

        self.append(Operation(*args, **kwargs))

    def put(self, item: Operation) -> None:
        """synonym for append."""
        self.append(item)

    def append(self, item: Operation) -> None:  # type: ignore
        """Restrict our diet to Operation objects only."""

        super().append(item)

    def apply(self) -> Operation:
        """Apply the next operation in the queue and remove it."""

        operation = self.popleft()
        operation()
        return operation

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

        if self.dry_run:
            logger.info('Dry run enabled, not applying op_queue')
            return False

        ans = self.yes or click.confirm(
            'Do you want to apply all these operations?', default=False)

        if ans:
            self.apply_all()
        return ans


op_queue = Operations()


def confirm_operations(func):
    """Decorator which confirms and applies queued operations after the
    function.

    ```python
    from duqtools.operations import confirm_operations, op_queue

    @confirm_operations
    def complicated_stuff()
        op_queue.add(print, args=('Hello World,),
                description="Function that prints hello world")
        op_queue.add(print, args=('Hello World again,),
                description="Function that prints hello world, again")
    ```
    """

    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        op_queue.confirm_apply_all()
        op_queue.clear()
        return ret

    return wrapper


def add_to_op_queue(description: str):
    """Decorator which adds the function call to the op_queue, instead of
    executing it directly, the string can be a format string and use the
    function arguments.

    ```python
    from duqtools.operations import add_to_op_queue, op_queue

    @add_to_op_queue("Printing hello world {name}")
    def print_hello_world(name):
        print(f"Hello World {name}")


    print_hello_world("Snoozy")

    op_queue.confirm_apply_all()
    ```
    """

    def op_queue_real(func):

        def wrapper(*args, **kwargs) -> None:
            # For the description format we must convert args to kwargs
            sig = signature(func)
            args_to_kw = dict(zip(sig.parameters, args))
            fkwargs = kwargs.copy()
            fkwargs.update(args_to_kw)
            formatted_description = description.format(**fkwargs)

            # add the function to the queue
            op_queue.add(action=func,
                         args=args,
                         kwargs=kwargs,
                         description=formatted_description)

        return wrapper

    return op_queue_real
