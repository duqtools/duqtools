import argparse
import logging
from logging import debug

import duqtools.config as cfg

from .create import create
from .init import init
from .status import status
from .submit import submit


def analyze():
    raise NotImplementedError


def cmdline():
    parser = argparse.ArgumentParser()

    # Subparsers
    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser('init',
                                        help='Create a default config file')
    parser_init.set_defaults(func=init)

    parser_create = subparsers.add_parser('create',
                                          help='Create the UQ run files')
    parser_create.set_defaults(func=create)

    parser_submit = subparsers.add_parser('submit', help='Submit the UQ runs')
    parser_submit.set_defaults(func=submit)

    parser_status = subparsers.add_parser(
        'status', help='Print the status of the UQ runs')
    parser_status.set_defaults(func=status)

    parser_analyze = subparsers.add_parser(
        'analyze', help='Analyze the results and generate a report')
    parser_analyze.set_defaults(func=analyze)

    # Globally required options
    parser.add_argument('CONFIG', type=str, help='path to store run files')

    # Global optional options
    parser.add_argument('--debug',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Enable debug print statements')
    parser.add_argument('--force',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Force the action you want to take')

    # parse the arguments
    args = parser.parse_args()

    # Set the debug level
    if (args.debug):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    debug('Arguments after parsing: %s' % args)

    # Load the config file
    if not args.func == init:  # dont read it if we have to create it
        cfg.Config(args.CONFIG)

    # Run the subcommand
    args.func(args=args)


if __name__ == '__main__':
    cmdline()
