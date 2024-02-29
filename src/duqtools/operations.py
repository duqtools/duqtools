"""Submodule for handling queuing and jobs.

*Duqtools* uses delayed operations for filesystem-changing operations.
They are implemented mostly with decorators, but a function could be added directly
to the `op_queue`.
"""

from __future__ import annotations

import atexit
import logging
from collections import deque
from contextlib import contextmanager
from inspect import signature
from typing import Any, Callable, Optional, Sequence

import click
from pydantic import Field, field_validator

from ._logging_utils import duqlog_screen
from .schema import BaseModel

logger = logging.getLogger(__name__)

OP_STYLE = {'fg': 'green'}

INFO_STYLE = {'fg': 'blue'}

NO_OP_STYLE = {
    'fg': 'red',
    'bold': True,
}

HEADER_STYLE = {
    'fg': 'red',
    'bold': True,
}

loginfo = duqlog_screen.info
logwarning = duqlog_screen.warning
style = click.style


class LongDescription(BaseModel):
    description: str = Field(
        description='description of the operation to be done')
    extra_description: Optional[str] = Field(None,
                                             description='Extra description')
    style: dict[str, Any] = Field(OP_STYLE,
                                  description='Styling for op description')

    @property
    def long_description(self) -> str:
        description = style(self.description, **self.style)

        if self.extra_description:
            description = f'{description} : {self.extra_description}'

        return description


class Warning(LongDescription):
    """Warning item for screen log."""
    style: dict[str, Any] = NO_OP_STYLE

    def __hash__(self):
        return hash((self.description, self.extra_description))

    def __eq__(self, other):
        return hash(self) == hash(other)


class Operation(LongDescription):
    """Operation, simple class which has a callable action.

    Usually not called directly but used through Operations.
    """
    quiet: bool = Field(False,
                        description='print out this operation to the screen')

    action: Optional[Callable] = Field(
        None,
        description='a function which can be executed when we '
        'decide to apply this operation')

    args: Optional[Sequence] = Field(
        None,
        validate_default=True,
        description='positional arguments that have to be '
        'passed to the action')

    kwargs: Optional[dict] = Field(
        None,
        validate_default=True,
        description='keyword arguments that will be '
        'passed to the action')

    def __call__(self) -> Operation:
        """Execute the action with the args and kwargs.

        Returns
        -------
        Operation
            The operation that was executed
        """
        if self.action:
            logger.debug(self.long_description)
            self.action(*self.args, **self.kwargs)  # type: ignore
        return self

    @field_validator('args')
    def validate_args(cls, v):
        if v is None:
            v = ()
        return v

    @field_validator('kwargs')
    def validate_kwargs(cls, v):
        if v is None:
            v = {}
        return v


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
    enabled = False  # Actually do something
    dry_run = False  # Never apply any operations (do not even ask)
    warnings: set[Warning] = set()

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Operations._instance:
            Operations._instance = super().__new__(cls)
        return Operations._instance

    @property
    def n_actions(self):
        """Return number of actions (no no-op)."""
        return sum(op.action is not None for op in self)

    def add(self, **kwargs) -> None:
        """Convenience Operation wrapper around .append().

        ```python
        from duqtools.operations import add_to_op_queue.

        op_queue.add(action=print, args=('Hello World,),
        description="Function that prints hello world")
        ```
        """
        self.append(Operation(**kwargs))

    def add_no_op(self,
                  description: str,
                  extra_description: str | None = None):
        """Adds a line to specify an action will not be undertaken."""
        self.add(action=None,
                 description=description,
                 extra_description=extra_description,
                 style=NO_OP_STYLE)

    def info(self, description: str, extra_description: Optional[str] = None):
        """Adds an info line."""
        self.add(action=None,
                 description=description,
                 extra_description=extra_description,
                 style=INFO_STYLE)

    def warning(self, description: str, extra_description: str):
        self.warnings.add(
            Warning(description=description,
                    extra_description=extra_description))

    def put(self, item: Operation):
        """Synonym for append."""
        self.append(item)

    def append(self, item: Operation):  # type: ignore
        """Restrict our diet to Operation objects only."""
        if self.enabled:
            logger.debug(
                f'Appended {item.description} to the operations queue')
            super().append(item)
        else:
            loginfo('- ' + item.long_description)
            item()

    def apply(self) -> Operation:
        """Apply the next operation in the queue and remove it."""
        op = self.popleft()
        op()
        return op

    def _apply_all(self, callback: Optional[Callable] = None) -> None:
        """Pop and apply all operations in the queue."""
        while self:
            op = self.apply()
            if callback:
                callback(op)

    def apply_all(self) -> None:
        """Apply all queued operations and empty the queue.

        and show a fancy progress bar while applying
        """
        from tqdm import tqdm
        loginfo(style('Applying Operations', **HEADER_STYLE))  # type: ignore

        with tqdm(total=self.n_actions, position=1) as pbar:
            pbar.set_description('Progress')

            with tqdm(bar_format='{desc}') as dbar:

                def callback(op):
                    if not op.action:
                        return
                    if not op.quiet:
                        dbar.set_description(op.long_description)
                    pbar.update()

                self._apply_all(callback=callback)

    def confirm_apply_all(self) -> bool:
        """First asks the user if he wants to apply everything.

        Returns
        -------
        bool: did we apply everything or not
        """
        # To print the descriptions we need to get them
        loginfo('')
        loginfo(style('Operations in the Queue:',
                      **HEADER_STYLE))  # type: ignore
        loginfo(style('========================',
                      **HEADER_STYLE))  # type: ignore
        for op in self:
            if not op.quiet:
                loginfo('- ' + op.long_description)

        for warning in self.warnings:
            loginfo('- ' + warning.long_description)

        if self.dry_run:
            loginfo('Dry run enabled, not applying op_queue')
            return False

        # Do not confirm if all actions are no-op
        if all(op.action is None for op in self):
            loginfo('\nNo actions to execute.')
            return False

        if n_no_op := sum(op.action is None for op in self):
            loginfo(
                f'\nThere are {n_no_op} operations that will not be applied.')

        is_confirmed = self.yes or click.confirm(
            f'\nDo you want to apply all {self.n_actions} operations?',
            default=False)

        if is_confirmed:
            self.apply_all()

        return is_confirmed

    def check_unconfirmed_operations(self):
        """Safety check, it should never happen that operations are not
        executed."""
        if self:
            logwarning(
                style((f'There are still {self.n_actions} operations '
                       'in the queue at program exit!'), **HEADER_STYLE))


op_queue = Operations()


def confirm_operations(func):
    """Decorator which confirms and applies queued operations after the
    function.

    ```python
    from duqtools.operations import confirm_operations, op_queue

    @confirm_operations
    def complicated_stuff()
        op_queue.add(action=print, args=('Hello World,),
                description="Function that prints hello world")
        op_queue.add(action=print, args=('Hello World again,),
                description="Function that prints hello world, again")
    ```
    """

    def wrapper(*args, **kwargs):
        if op_queue.enabled:
            raise RuntimeError('op_queue already enabled')
        try:
            op_queue.enabled = True
            ret = func(*args, **kwargs)
            op_queue.confirm_apply_all()
            op_queue.clear()
            op_queue.enabled = False
        except Exception:
            op_queue.clear()
            op_queue.enabled = False
            raise
        return ret

    return wrapper


def add_to_op_queue(op_desc: str, extra_desc: str | None = None, quiet=False):
    """Decorator which adds the function call to the op_queue, instead of
    executing it directly, the string can be a format string and use the
    function arguments.

    ```python
    from duqtools.operations import add_to_op_queue, op_queue

    @add_to_op_queue("Printing hello world", "{name}")
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
            extra_formatted = None
            if extra_desc:
                extra_formatted = extra_desc.format(**fkwargs)
            op_formatted = op_desc.format(**fkwargs)

            # add the function to the queue
            op_queue.add(action=func,
                         args=args,
                         kwargs=kwargs,
                         description=op_formatted,
                         extra_description=extra_formatted,
                         quiet=quiet)

        return wrapper

    return op_queue_real


atexit.register(op_queue.check_unconfirmed_operations)


@contextmanager
def op_queue_context():
    """Context manager to enable the op_queue, and confirm_operations on exit
    Also disables the op_queue on exit.

    Works more or less the same as the `@confirm_operations` decorator
    """
    if op_queue.enabled:
        raise RuntimeError('op_queue already enabled')
    try:
        op_queue.enabled = True
        yield
        op_queue.confirm_apply_all()
        op_queue.clear()
        op_queue.enabled = False
    except Exception:
        op_queue.clear()
        op_queue.enabled = False
        raise
