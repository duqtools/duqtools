import argparse
from duqtools.config import Config

def create():
  pass

def submit():
  pass

def analyze():
  pass

def parse():
  parser = argparse.ArgumentParser()

  # Globally required options
  parser.add_argument('CONFIG', type=str, help='path to store run files')

  # Subparsers
  subparsers = parser.add_subparsers()
  parser_create  = subparsers.add_parser('create' , help='Create the UQ run files')
  parser_create.set_defaults(func=create)

  parser_submit  = subparsers.add_parser('submit' , help='Submit the UQ runs')
  parser_submit.set_defaults(func=submit)

  parser_analyze = subparsers.add_parser('analyze', help='Analyze the results and generate a report')
  parser_analyze.set_defaults(func=analyze)

  # parse the arguments
  args = parser.parse_args()
  print("Arguments after parsing: ", args)

  # Load the config file
  global config
  config = Config(args.CONFIG)

  # Run the subcommand
  args.func()


if __name__ == '__main__':
  parse()
