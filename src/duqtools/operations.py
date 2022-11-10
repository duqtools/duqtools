from __future__ import annotations

import atexit
import logging
from collections import deque
from contextlib import contextmanager
from inspect import signature
from typing import Callable, Optional, Sequence

import click
from pydantic import Field, validator

from ._logging_utils import duqlog_screen
from .config import cfg
from .schema import BaseModel

logger = logging.getLogger(__name__)

OP_STYLE = {'fg': 'green'}

NO_OP_STYLE = {
    'fg': 'red',
    'bold': True,
}

HEADER_STYLE = {
    'fg': 'red',
    'bold': True,
}


class Operation(BaseModel):
    """Operation, simple class which has a callable action.

    Usually not called directly but used through Operations. has the
    following members:
    """

    quiet: bool = Field(False,
                        description='print out this operation to the screen')
    description: str = Field(
        description='description of the operation to be done')
    action: Optional[Callable] = Field(
        description='a function which can be executed when we '
        'decide to apply this operation')
    extra_description: Optional[str] = Field(description='Extra description')
    args: Optional[Sequence] = Field(
        None,
        description='positional arguments that have to be '
        'passed to the action')
    kwargs: Optional[dict] = Field(
        None,
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

    @property
    def long_description(self):
        style = NO_OP_STYLE if self.action is None else OP_STYLE

        description = click.style(self.description, **style)

        if self.extra_description is not None:
            description = f'{description} : {self.extra_description}'

        return description

    @validator('args', always=True)
    def validate_args(cls, v):
        if v is None:
            v = ()
        return v

    @validator('kwargs', always=True)
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

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Operations._instance:
            Operations._instance = super().__new__(cls)
        return Operations._instance

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
                  extra_description: Optional[str] = None):
        """Adds a line to specify an action will not be undertaken."""
        self.add(action=None,
                 description=description,
                 extra_description=extra_description)

    def put(self, item: Operation):
        """synonym for append."""
        self.append(item)

    def append(self, item: Operation):  # type: ignore
        """Restrict our diet to Operation objects only."""
        if self.enabled:
            logger.debug(
                f'Appended {item.description} to the operations queue')
            super().append(item)
        else:
            duqlog_screen.info('- ' + item.long_description)
            item()

    def apply(self) -> Operation:
        """Apply the next operation in the queue and remove it."""

        operation = self.popleft()
        operation()
        return operation

    def apply_all(self) -> None:
        """Apply all queued operations and empty the queue.

        and show a fancy progress bar while applying
        """
        from tqdm import tqdm
        duqlog_screen.info(click.style('Applying Operations', **HEADER_STYLE))
        if not cfg.quiet:
            with tqdm(total=len(self), position=1) as pbar:
                pbar.set_description('Applying operations')
                with tqdm(iterable=False, bar_format='{desc}',
                          position=0) as dbar:
                    while len(self) != 0:
                        op = self.popleft()
                        if not op.quiet:
                            dbar.set_description(op.long_description)
                        logger.info(op.long_description)
                        pbar.update()
                        op()
        else:
            while len(self) != 0:
                op = self.popleft()
                op()

    def confirm_apply_all(self) -> bool:
        """First asks the user if he wants to apply everything.

        Returns
        -------
        bool: did we apply everything or not
        """

        # To print the descriptions we need to get them
        duqlog_screen.info('')
        duqlog_screen.info(
            click.style('Operations in the Queue:', **HEADER_STYLE))
        duqlog_screen.info(
            click.style('========================', **HEADER_STYLE))
        for op in self:
            if not op.quiet:
                duqlog_screen.info('- ' + op.long_description)

        if self.dry_run:
            duqlog_screen.info('Dry run enabled, not applying op_queue')
            return False

        # Do not confirm if all actions are no-op
        if all(op.action is None for op in self):
            duqlog_screen.info('\nNo actions to execute.')
            return False

        ans = self.yes or click.confirm(
            '\nDo you want to apply all these operations?', default=False)

        if ans:
            self.apply_all()

        return ans

    def check_unconfirmed_operations(self):
        """Safety check, it should never happen that operations are not
        executed."""
        if len(self) != 0:
            duqlog_screen.warning(
                click.style((f'There are still {len(self)} operations '
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


def add_to_op_queue(op_desc: str,
                    extra_desc: Optional[str] = None,
                    quiet=False):
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
