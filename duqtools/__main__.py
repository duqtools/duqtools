import argparse
from duqtools.config import Config

def parse():

  parser = argparse.ArgumentParser()

  # Globally required options
  parser.add_argument('CONFIG', type=str, help='path to store run files')

  # Subparsers
  subparsers = parser.add_subparsers()
  parser_create  = subparsers.add_parser('create' , help='Create the UQ run files')
  parser_submit  = subparsers.add_parser('submit' , help='Submit the UQ runs')
  parser_analyze = subparsers.add_parser('analyze', help='Analyze the results and generate a report')
  args = parser.parse_args()


  # Load the config file
  global config
  config = Config(args.CONFIG)


if __name__ == '__main__':
  parse()
