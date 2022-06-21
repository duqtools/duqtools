import argparse
import logging

import coverage

from duqtools.config import cfg

from .create import create
from .init import init
from .plot import plot
from .status import Status
from .submit import submit

logger = logging.getLogger(__name__)
coverage.process_startup()


def cmdline():

    parser = argparse.ArgumentParser(conflict_handler='resolve')

    # Subparsers
    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser('init',
                                        help='Create a default config file',
                                        parents=[parser],
                                        conflict_handler='resolve')
    parser_init.set_defaults(func=init)

    parser_create = subparsers.add_parser('create',
                                          help='Create the UQ run files',
                                          parents=[parser],
                                          conflict_handler='resolve')
    parser_create.set_defaults(func=create)

    parser_submit = subparsers.add_parser('submit',
                                          help='Submit the UQ runs',
                                          parents=[parser],
                                          conflict_handler='resolve')
    parser_submit.set_defaults(func=submit)

    parser_status = subparsers.add_parser(
        'status',
        help='Print the status of the UQ runs',
        parents=[parser],
        conflict_handler='resolve')
    parser_status.set_defaults(func=Status.status)
    parser_status.add_argument('--progress',
                               action='store_const',
                               const=True,
                               default=False,
                               help='Fancy progress bar')

    parser_plot = subparsers.add_parser(
        'plot', help='Analyze the results and generate a report')
    parser_plot.set_defaults(func=plot)

    # Global optional options
    parser.add_argument('-c',
                        '--config',
                        type=str,
                        help='Path to config',
                        default='duqtools.yaml')
    parser.add_argument('--debug',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Enable debug print statements')
    parser.add_argument('-f',
                        '--force',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Force the action you want to take')

    # parse the arguments
    args = parser.parse_args()

    # Set the debug level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug('Arguments after parsing: %s' % args)

    # Load the config file
    if not args.func == init:  # dont read it if we have to create it
        cfg.read(args.config)

    # Run the subcommand
    args.func(args=args)


if __name__ == '__main__':
    cmdline()
