import os

import yaml


# get_config()
#_____________________________________________________________________________________
def get_config(config={}):
    home_dir = os.environ.get('HOME')
    if not home_dir:
        return config
    config_file = os.path.join(home_dir, '.config', 'internetarchive.yml')
    try:
        config = yaml.load(open(config_file));
    except IOError:
        config_file = os.path.join(home_dir, '.internetarchive.yml')
        try:
            config = yaml.load(open(config_file))
        except IOError:
            return config
    return config
