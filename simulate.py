import argparse
from events import EventManager
from file_input import read_network
from io import StringIO
from contextlib import redirect_stdout

parser = argparse.ArgumentParser(description='Run network simulation.')
parser.add_argument('input_file', type=str, help='JSON input file for network')
parser.add_argument('--debug', action='store_true', help='Enable debug output')
args = parser.parse_args()

if __name__ == '__main__':
    em = EventManager()
    read_network(args.input_file, em, args.debug)

    em.run()

    print(em.current_time)

