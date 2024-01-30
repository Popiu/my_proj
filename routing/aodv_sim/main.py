import os
import json

from Tester import Tester

ABS_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ABS_PATH, 'configs')

if __name__ == '__main__':
    test_config_filename = os.path.join(CONFIG_PATH, 'test_config.json')
    with open(test_config_filename, 'r') as f:
        test_config = json.load(f)

    tester = Tester(
        test_config, log_dir=ABS_PATH
    )
    tester.main()