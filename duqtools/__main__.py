import argparse
import logging
import sys
from functools import partial

import coverage

from duqtools.config import cfg

from .cleanup import cleanup
from .create import create
from .dash import dash
from .init import init
from .plot import plot
from .status import status
from .submit import submit

logger = logging.getLogger(__name__)
coverage.process_startup()


def cmdline():

    parser = argparse.ArgumentParser()
    parser.set_defaults(func=None)

    # Global optional options
    parser.add_argument('-c',
                        '--config',
                        type=str,
                        help='Path to config',
                        default='duqtools.yaml')
    parser.add_argument('--debug',
                        action='store_true',
                        default=False,
                        help='Enable debug print statements')
    parser.add_argument('-f',
                        '--force',
                        action='store_true',
                        default=False,
                        help='Force the action you want to take')

    # Subparsers
    subparsers = parser.add_subparsers()

    add_subparser = partial(subparsers.add_parser,
                            parents=[parser],
                            conflict_handler='resolve')

    parser_init = add_subparser(
        'init',
        help='Create a default config file',
    )
    parser_init.set_defaults(func=init)
    parser_init.add_argument(
        '--full',
        action='store_true',
        default=False,
        help='Create a config file with all possible config values')

    parser_create = add_subparser(
        'create',
        help='Create the UQ run files',
    )
    parser_create.set_defaults(func=create)

    parser_submit = add_subparser(
        'submit',
        help='Submit the UQ runs',
    )
    parser_submit.set_defaults(func=submit)

    parser_status = add_subparser(
        'status',
        help='Print the status of the UQ runs',
    )
    parser_status.set_defaults(func=status)
    parser_status.add_argument('--progress',
                               action='store_true',
                               default=False,
                               help='Fancy progress bar')
    parser_status.add_argument('--detailed',
                               action='store_true',
                               default=False,
                               help='detailed info on progress')

    parser_plot = add_subparser(
        'plot',
        help='Analyze the results and generate a report',
    )
    parser_plot.set_defaults(func=plot)

    parser_clean = add_subparser(
        'clean',
        help='Delete generated IDS data and the run dirs',
    )

    parser_clean.add_argument('--out',
                              action='store_true',
                              default=False,
                              help='Remove output data.')

    parser_clean.set_defaults(func=cleanup)

    parser_dash = add_subparser(
        'dash',
        help='Open dashboard for evaluating IDS data',
    )
    parser_dash.set_defaults(func=dash)

    # parse the arguments
    options = parser.parse_args()

    # Set the debug level
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug('Arguments after parsing: %s', options)

    if not options.func:
        parser.print_help()
        sys.exit(0)

    # Load the config file
    if not options.func == init:  # dont read it if we have to create it
        cfg.read(options.config)

    # Run the subcommand
    options.func(**vars(options))


if __name__ == '__main__':
    cmdline()
