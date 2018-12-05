from events import EventManager
from file_input import read_network
from io import StringIO
from contextlib import redirect_stdout


if __name__ == '__main__':
    em = EventManager()
    read_network('test_case_1_reno.json', em)

    em.run()

    print(em.current_time)



