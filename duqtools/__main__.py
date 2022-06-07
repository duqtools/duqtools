import argparse
from logging import debug
import logging
import duqtools.config as cfg
from duqtools.submit import submit
from duqtools.status import status

def create():
  pass

def analyze():
  pass

def cmdline():
  parser = argparse.ArgumentParser()


  # Subparsers
  subparsers = parser.add_subparsers()
  parser_create  = subparsers.add_parser('create' , help='Create the UQ run files')
  parser_create.set_defaults(func=create)

  parser_submit  = subparsers.add_parser('submit' , help='Submit the UQ runs')
  parser_submit.set_defaults(func=submit)

  parser_submit  = subparsers.add_parser('status' , help='Print the status of the UQ runs')
  parser_submit.set_defaults(func=status)

  parser_analyze = subparsers.add_parser('analyze', help='Analyze the results and generate a report')
  parser_analyze.set_defaults(func=analyze)

  # Globally required options
  parser.add_argument('CONFIG', type=str, help='path to store run files')

  # Global optional options
  parser.add_argument('--debug', action='store_const', const=True, default=False, help='Enable debug print statements')
  parser.add_argument('--force', action='store_const', const=True, default=False, help='Force the action you want to take')

  # parse the arguments
  args = parser.parse_args()

  # Set the debug level
  if (args.debug):
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO)

  debug("Arguments after parsing: %s"%args)

  # Load the config file
  cfg.Config(args.CONFIG)

  # Run the subcommand
  args.func()

if __name__ == '__main__':
  cmdline()
